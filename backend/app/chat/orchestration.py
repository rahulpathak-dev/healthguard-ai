import asyncio
import json
import uuid
from collections.abc import AsyncIterator, Sequence
from urllib.parse import urlparse

from sqlalchemy import select

from app.ai_safety.engine import analyze_input, log_safety_event, review_output
from app.chat.models import ChatCitation, ChatMessage
from app.chat.provider import SYSTEM_POLICY, ProviderCitation, ProviderRequest, provider
from app.core.logging import get_logger
from app.db.session import SessionFactory
from app.rag.service import RetrievalResult, retrieve

logger = get_logger()
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CHARACTERS = 12_000
MAX_RESPONSE_CHARACTERS = 6_000
ALLOWED_CITATION_HOSTS = {
    "medlineplus.gov",
    "www.who.int",
    "who.int",
    "www.nhs.uk",
    "www.cdc.gov",
    "cdc.gov",
}


def clean_text(value: str) -> str:
    return "".join(
        character for character in value if character in "\n\t" or ord(character) >= 32
    ).strip()


def bounded_history(messages: Sequence[ChatMessage]) -> tuple[tuple[str, str], ...]:
    selected: list[tuple[str, str]] = []
    used = 0
    for message in reversed(messages[-MAX_HISTORY_MESSAGES:]):
        content = clean_text(message.content)
        remaining = MAX_HISTORY_CHARACTERS - used
        if remaining <= 0:
            break
        content = content[:remaining]
        selected.append((message.role, content))
        used += len(content)
    selected.reverse()
    return tuple(selected)


def safe_citation(value: ProviderCitation) -> bool:
    parsed = urlparse(value.url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_CITATION_HOSTS


def event(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n").encode()


async def _collect_generation(request: ProviderRequest) -> tuple[str, tuple[ProviderCitation, ...]]:
    content = ""
    citations: list[ProviderCitation] = []
    async for delta in provider.stream(request):
        if delta.text:
            remaining = MAX_RESPONSE_CHARACTERS - len(content)
            if remaining <= 0:
                break
            content += delta.text[:remaining]
        elif delta.citation and safe_citation(delta.citation):
            citations.append(delta.citation)
    return content, tuple(citations)


async def stream_assistant(
    assistant_id: uuid.UUID,
    user_text: str,
    language: str,
    history: Sequence[ChatMessage],
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> AsyncIterator[bytes]:
    cleaned_user_text = clean_text(user_text)
    yield event({"type": "start", "message_id": str(assistant_id)})
    content = ""
    citations: tuple[ProviderCitation, ...] = ()
    try:
        input_analysis = analyze_input(cleaned_user_text)
        async with SessionFactory() as db:
            await log_safety_event(
                db,
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=assistant_id,
                stage="input_analysis",
                analysis=input_analysis,
                text=cleaned_user_text,
                metadata={"language": language},
            )
            await db.commit()
        if input_analysis.safe_fallback:
            retrieval = RetrievalResult(
                evidence=(), no_answer=True, low_confidence=True, top_score=0.0
            )
            raw_content = input_analysis.safe_fallback
            raw_citations: tuple[ProviderCitation, ...] = ()
        else:
            async with SessionFactory() as db:
                retrieval = await retrieve(
                    db,
                    query=cleaned_user_text,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )
                await db.commit()
            evidence_citations = tuple(
                ProviderCitation(
                    title=item.title,
                    source=item.source,
                    url=item.url,
                    excerpt=item.excerpt,
                )
                for item in retrieval.evidence
            )
            request = ProviderRequest(
                system_policy=SYSTEM_POLICY,
                user_text=cleaned_user_text,
                language=language,
                history=bounded_history(history),
                evidence=evidence_citations,
                no_answer=retrieval.no_answer,
                low_confidence=retrieval.low_confidence,
            )
            raw_content, raw_citations = await _collect_generation(request)
        review = review_output(
            raw_content,
            raw_citations,
            input_analysis=input_analysis,
            retrieval=retrieval,
        )
        content = review.text
        citations = review.citations
        async with SessionFactory() as db:
            await log_safety_event(
                db,
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=assistant_id,
                stage="output_review",
                analysis=review,
                text=content,
                metadata={"confidence": review.confidence, "citation_count": len(citations)},
            )
            await db.commit()
        for start in range(0, len(content), 64):
            await asyncio.sleep(0)
            yield event({"type": "delta", "text": content[start : start + 64]})
        for citation in citations:
            yield event(
                {
                    "type": "citation",
                    "citation": {
                        "title": citation.title,
                        "source": citation.source,
                        "url": citation.url,
                        "excerpt": citation.excerpt,
                    },
                }
            )
        yield event(
            {
                "type": "safety",
                "confidence": review.confidence,
                "categories": list(review.categories),
                "action": review.action,
            }
        )
        async with SessionFactory() as db:
            message = await db.get(ChatMessage, assistant_id)
            if message:
                message.content = content
                message.status = "complete"
                message.estimated_tokens = max(1, len(content) // 4)
                db.add_all(
                    [
                        ChatCitation(
                            message_id=assistant_id,
                            title=item.title[:240],
                            source=item.source[:120],
                            url=item.url[:2048],
                            excerpt=item.excerpt[:500],
                        )
                        for item in citations
                    ]
                )
                await db.commit()
        yield event({"type": "done", "message_id": str(assistant_id)})
    except asyncio.CancelledError:
        async with SessionFactory() as db:
            message = await db.get(ChatMessage, assistant_id)
            if message:
                message.status = "interrupted"
                message.content = content or "The response was interrupted before completion."
                await db.commit()
        raise
    except Exception as exc:
        logger.exception(
            "chat_generation_failed", assistant_id=str(assistant_id), error_type=type(exc).__name__
        )
        async with SessionFactory() as db:
            message = await db.get(ChatMessage, assistant_id)
            if message:
                message.status = "failed"
                message.content = "The response could not be completed. Please try again."
                await db.commit()
        yield event({"type": "error", "message": "The response could not be completed."})


async def recent_history(conversation_id: uuid.UUID) -> list[ChatMessage]:
    async with SessionFactory() as db:
        rows = (
            await db.scalars(
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation_id, ChatMessage.status == "complete"
                )
                .order_by(ChatMessage.sequence.desc())
                .limit(MAX_HISTORY_MESSAGES)
            )
        ).all()
        return list(reversed(rows))
