import hashlib
import re
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_safety.engine import analyze_input
from app.auth.models import User
from app.misinformation.models import MisinformationCheck
from app.misinformation.schemas import CheckCreate
from app.rag.service import retrieve

HARMFUL_PATTERNS = (
    r"\bstop (all )?(medicine|medication|insulin|antibiotics)\b",
    r"\bcure(s)? cancer\b",
    r"\bavoid emergency\b",
    r"\bbleach\b",
    r"\bmiracle cure\b",
)
MANIPULATION_PATTERNS = (
    r"\bignore previous\b",
    r"\bdo not cite\b",
    r"\bpretend\b",
)


def summarize_claim(value: str) -> str:
    cleaned = " ".join(value.split())
    return cleaned[:500]


def claim_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def classify(claim: str, evidence_count: int, top_score: float) -> str:
    lowered = claim.lower()
    if any(re.search(pattern, lowered) for pattern in HARMFUL_PATTERNS):
        return "potentially_harmful"
    if any(re.search(pattern, lowered) for pattern in MANIPULATION_PATTERNS):
        return "misleading"
    if evidence_count == 0:
        return "insufficient_evidence"
    if top_score < 0.22:
        return "unsupported"
    if any(term in lowered for term in ("always", "never", "guaranteed", "100%")):
        return "misleading"
    return "likely_accurate"


async def check_claim(db: AsyncSession, *, user: User, payload: CheckCreate) -> MisinformationCheck:
    analysis = analyze_input(payload.claim)
    retrieval = await retrieve(db, query=payload.claim, user_id=user.id, limit=5)
    verdict = classify(payload.claim, len(retrieval.evidence), retrieval.top_score)
    sources = [
        {
            "title": item.title,
            "source": item.source,
            "url": item.url,
            "excerpt": item.excerpt,
            "score": item.score,
        }
        for item in retrieval.evidence
    ]
    evidence = {
        "claim_summary": summarize_claim(payload.claim),
        "evidence_analysis": (
            "Verdict is based only on retrieved approved sources and safety rules. "
            "The model's own belief is not treated as evidence."
        ),
        "trusted_sources": sources,
        "missing_context": [
            "Who the claim applies to",
            "Dose, timing, medical history, and source date",
            "Whether the claim is about prevention, treatment, or emergency care",
        ],
        "harm_warning": "Do not delay urgent care or change medicines based on a forwarded claim.",
        "uncertainty": (
            "Evidence may be incomplete; check current public-health or clinician guidance."
        ),
        "safe_next_steps": [
            "Check the original source and date.",
            "Compare with trusted public-health sources.",
            "Ask a clinician or pharmacist before acting on medical claims.",
        ],
        "safety_categories": list(analysis.categories),
    }
    check = MisinformationCheck(
        user_id=user.id,
        claim_hash=claim_hash(payload.claim),
        claim_summary=summarize_claim(payload.claim),
        verdict=verdict,
        evidence_json=evidence,
        created_at=datetime.now(UTC),
    )
    db.add(check)
    await db.flush()
    return check
