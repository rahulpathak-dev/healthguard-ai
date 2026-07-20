from datetime import UTC, datetime, timedelta

import pytest

from app.chat.provider import EducationProvider, ProviderRequest
from app.rag.models import KnowledgeSource
from app.rag.service import (
    APPROVED,
    MIN_CONFIDENCE,
    chunk_text,
    cosine,
    embed_text,
    ingest_document,
    normalize_content,
    trusted_url,
)


def approved_source() -> KnowledgeSource:
    return KnowledgeSource(
        name="MedlinePlus",
        publisher="U.S. National Library of Medicine",
        base_url="https://medlineplus.gov",
        approval_status=APPROVED,
        freshness_days=365,
        last_reviewed_at=datetime.now(UTC) - timedelta(days=10),
        created_at=datetime.now(UTC),
    )


def test_normalization_and_chunking_are_bounded_and_overlapping() -> None:
    messy = " Fever\n\n cough\t" + " word" * 260
    normalized = normalize_content(messy)
    chunks = chunk_text(messy, max_words=80, overlap_words=20)
    assert "\n" not in normalized
    assert len(chunks) > 1
    assert chunks[0].split()[-20:] == chunks[1].split()[:20]


def test_embeddings_are_stable_normalized_vectors() -> None:
    first = embed_text("fever cough hydration")
    second = embed_text("fever cough hydration")
    unrelated = embed_text("passport renewal office")
    assert first == second
    assert cosine(first, second) > 0.99
    assert cosine(first, unrelated) < cosine(first, second)


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://medlineplus.gov/fever.html", True),
        ("https://www.cdc.gov/flu/signs-symptoms/index.html", True),
        ("https://random-health-blog.example/fever", False),
        ("http://medlineplus.gov/fever.html", False),
        ("https://medlineplus.gov.example.com/fever", False),
    ],
)
def test_trusted_url_allows_only_exact_public_health_hosts(url: str, allowed: bool) -> None:
    assert trusted_url(url) is allowed


@pytest.mark.asyncio
async def test_ingestion_rejects_unapproved_sources_before_storage() -> None:
    source = approved_source()
    source.approval_status = "pending"
    with pytest.raises(ValueError, match="approved trusted medical sources"):
        await ingest_document(
            None,  # type: ignore[arg-type]
            source=source,
            title="Fever",
            url="https://medlineplus.gov/fever.html",
            content="Fever is a body temperature above normal.",
        )


@pytest.mark.asyncio
async def test_no_answer_response_distinguishes_uncertainty_and_next_step() -> None:
    provider = EducationProvider()
    request = ProviderRequest(
        system_policy="policy",
        user_text="What should I do about a rare issue?",
        language="en",
        history=(),
        no_answer=True,
        low_confidence=True,
    )
    text = "".join([event.text async for event in provider.stream(request) if event.text])
    assert "## Retrieved evidence" in text
    assert "## General explanation" in text
    assert "## Uncertainty" in text
    assert "## Recommended next step" in text
    assert "## Safety disclaimer" in text
    assert "could not find enough approved" in text


def test_confidence_threshold_is_conservative() -> None:
    assert 0 < MIN_CONFIDENCE < 0.5
