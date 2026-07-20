import hashlib
import math
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.models import KnowledgeChunk, KnowledgeDocument, KnowledgeSource, RetrievalLog

TRUSTED_HOSTS = {
    "medlineplus.gov",
    "www.who.int",
    "who.int",
    "www.nhs.uk",
    "www.cdc.gov",
    "cdc.gov",
}
APPROVED = "approved"
MIN_CONFIDENCE = 0.18
EMBEDDING_DIMENSIONS = 64


@dataclass(frozen=True)
class RetrievedEvidence:
    chunk_id: uuid.UUID
    title: str
    source: str
    publisher: str
    url: str
    excerpt: str
    score: float
    retrieved_at: datetime
    reviewed_at: datetime | None
    stale: bool


@dataclass(frozen=True)
class RetrievalResult:
    evidence: tuple[RetrievedEvidence, ...]
    no_answer: bool
    low_confidence: bool
    top_score: float


def normalize_content(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.replace("\x00", " ")).strip()
    return cleaned[:80_000]


def trusted_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in TRUSTED_HOSTS


def chunk_text(text: str, *, max_words: int = 180, overlap_words: int = 32) -> list[str]:
    words = normalize_content(text).split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, max_words - overlap_words)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + max_words]).strip()
        if chunk:
            chunks.append(chunk)
        if start + max_words >= len(words):
            break
    return chunks


def embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % EMBEDDING_DIMENSIONS
        vector[index] += 1.0
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [round(value / magnitude, 6) for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


async def ingest_document(
    db: AsyncSession,
    *,
    source: KnowledgeSource,
    title: str,
    url: str,
    content: str,
    metadata: dict[str, object] | None = None,
) -> KnowledgeDocument:
    if source.approval_status != APPROVED or not trusted_url(url):
        raise ValueError("Only approved trusted medical sources can be ingested")
    now = datetime.now(UTC)
    document = KnowledgeDocument(
        source_id=source.id,
        title=title[:240],
        url=url,
        normalized_text=normalize_content(content),
        status="active",
        retrieved_at=now,
        reviewed_at=source.last_reviewed_at,
        metadata_json=metadata or {},
    )
    db.add(document)
    await db.flush()
    db.add_all(
        KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk,
            embedding=embed_text(chunk),
            token_count=max(1, len(chunk) // 4),
            metadata_json={},
        )
        for index, chunk in enumerate(chunk_text(document.normalized_text))
    )
    return document


async def retrieve(
    db: AsyncSession,
    *,
    query: str,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None = None,
    limit: int = 4,
) -> RetrievalResult:
    query_vector = embed_text(query)
    rows = (
        await db.execute(
            select(KnowledgeChunk, KnowledgeDocument, KnowledgeSource)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeDocument.source_id)
            .where(
                KnowledgeSource.approval_status == APPROVED,
                KnowledgeDocument.status == "active",
            )
        )
    ).all()
    scored: list[tuple[float, KnowledgeChunk, KnowledgeDocument, KnowledgeSource]] = []
    now = datetime.now(UTC)
    for chunk, document, source in rows:
        if not trusted_url(document.url):
            continue
        score = cosine(query_vector, [float(value) for value in chunk.embedding])
        if document.reviewed_at and document.reviewed_at < now - timedelta(
            days=source.freshness_days
        ):
            score *= 0.85
        scored.append((score, chunk, document, source))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[:limit]
    top_score = selected[0][0] if selected else 0.0
    low_confidence = top_score < MIN_CONFIDENCE
    evidence = tuple(
        RetrievedEvidence(
            chunk_id=chunk.id,
            title=document.title,
            source=source.name,
            publisher=source.publisher,
            url=document.url,
            excerpt=chunk.content[:500],
            score=round(score, 4),
            retrieved_at=document.retrieved_at,
            reviewed_at=document.reviewed_at,
            stale=bool(
                document.reviewed_at
                and document.reviewed_at < now - timedelta(days=source.freshness_days)
            ),
        )
        for score, chunk, document, source in selected
        if score >= MIN_CONFIDENCE
    )
    result = RetrievalResult(
        evidence=evidence,
        no_answer=not evidence,
        low_confidence=low_confidence,
        top_score=round(top_score, 4),
    )
    db.add(
        RetrievalLog(
            user_id=user_id,
            conversation_id=conversation_id,
            query=normalize_content(query)[:500],
            filters_json={"approval_status": APPROVED, "trusted_hosts": sorted(TRUSTED_HOSTS)},
            result_count=len(evidence),
            top_score=result.top_score,
            no_answer=result.no_answer,
            created_at=now,
        )
    )
    return result
