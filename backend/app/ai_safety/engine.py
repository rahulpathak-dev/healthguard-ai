import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_safety.models import SafetyEvent
from app.chat.provider import ProviderCitation
from app.rag.service import TRUSTED_HOSTS, RetrievalResult

PROMPT_INJECTION_PATTERNS = (
    r"\bignore (all )?(previous|earlier|above) (instructions|rules)\b",
    r"\b(system|developer) prompt\b",
    r"\breveal (your|the) (prompt|instructions|policy)\b",
    r"\bact as\b.*\bdoctor\b",
)
EMERGENCY_PATTERNS = (
    r"\bchest pain\b",
    r"\bcannot breathe\b",
    r"\bcan't breathe\b",
    r"\bunconscious\b",
    r"\bsevere bleeding\b",
    r"\bstroke\b",
    r"\bface droop\b",
    r"\bblue lips\b",
)
SELF_HARM_PATTERNS = (
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bsuicide\b",
    r"\bself[- ]?harm\b",
)
UNSAFE_MEDICATION_PATTERNS = (
    r"\bhow much\b.*\b(take|dose|mg|tablet)\b",
    r"\boverdose\b",
    r"\bdouble (my )?dose\b",
    r"\bchild\b.*\b(dose|dosage|mg)\b",
)
HARMFUL_INSTRUCTION_PATTERNS = (
    r"\bpoison\b",
    r"\bmake .* toxin\b",
    r"\bhide symptoms\b",
    r"\bstop (my )?(heart|breathing)\b",
)
PREGNANCY_CHILD_PATTERNS = (
    r"\bpregnan(t|cy)\b",
    r"\bnewborn\b",
    r"\binfant\b",
    r"\btoddler\b",
    r"\bchild\b",
)
DIAGNOSIS_OUTPUT_PATTERNS = (
    r"\byou have\b",
    r"\byou are suffering from\b",
    r"\bthis is definitely\b",
    r"\bdiagnosis is\b",
)
DOSAGE_OUTPUT_PATTERNS = (
    r"\btake \d+(\.\d+)?\s?(mg|mcg|g|ml|tablets?)\b",
    r"\bincrease your dose\b",
    r"\bdouble your dose\b",
)
REQUIRED_SECTIONS = (
    "## Retrieved evidence",
    "## General explanation",
    "## Uncertainty",
    "## Recommended next step",
    "## Safety disclaimer",
)


@dataclass(frozen=True)
class SafetyAnalysis:
    categories: tuple[str, ...]
    severity: str
    action: str
    confidence: float
    safe_fallback: str | None = None


@dataclass(frozen=True)
class SafetyReview:
    text: str
    citations: tuple[ProviderCitation, ...]
    confidence: float
    categories: tuple[str, ...]
    action: str


def content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def analyze_input(text: str) -> SafetyAnalysis:
    categories: list[str] = []
    if _matches(PROMPT_INJECTION_PATTERNS, text):
        categories.append("prompt_injection")
    if _matches(SELF_HARM_PATTERNS, text):
        categories.append("self_harm")
    if _matches(EMERGENCY_PATTERNS, text):
        categories.append("emergency_red_flag")
    if _matches(UNSAFE_MEDICATION_PATTERNS, text):
        categories.append("unsafe_medication_request")
    if _matches(HARMFUL_INSTRUCTION_PATTERNS, text):
        categories.append("harmful_instruction")
    if _matches(PREGNANCY_CHILD_PATTERNS, text):
        categories.append("pregnancy_child_caution")
    if "self_harm" in categories:
        return SafetyAnalysis(tuple(categories), "critical", "fallback", 0.98, self_harm_fallback())
    if "emergency_red_flag" in categories:
        return SafetyAnalysis(tuple(categories), "critical", "fallback", 0.96, emergency_fallback())
    if "harmful_instruction" in categories:
        return SafetyAnalysis(tuple(categories), "high", "fallback", 0.94, harmful_fallback())
    if "unsafe_medication_request" in categories:
        return SafetyAnalysis(tuple(categories), "high", "caution", 0.88)
    if categories:
        return SafetyAnalysis(tuple(categories), "medium", "caution", 0.78)
    return SafetyAnalysis((), "low", "allow", 0.72)


def emergency_fallback() -> str:
    return (
        "## Retrieved evidence\n\n"
        "This request was routed by the safety engine before retrieval because it may "
        "describe an emergency.\n\n"
        "## General explanation\n\n"
        "Symptoms such as chest pain, trouble breathing, unconsciousness, stroke signs, "
        "or severe bleeding can require immediate in-person care.\n\n"
        "## Uncertainty\n\n"
        "An online assistant cannot determine how serious this is for you.\n\n"
        "## Recommended next step\n\n"
        "Contact local emergency services now or ask someone nearby to help you reach "
        "emergency care.\n\n"
        "## Safety disclaimer\n\n"
        "This is safety routing, not a diagnosis or treatment plan."
    )


def self_harm_fallback() -> str:
    return (
        "## Retrieved evidence\n\n"
        "This request was routed by the safety engine before retrieval because it may "
        "involve self-harm.\n\n"
        "## General explanation\n\n"
        "You deserve immediate support from a real person right now.\n\n"
        "## Uncertainty\n\n"
        "I cannot assess your immediate safety from here.\n\n"
        "## Recommended next step\n\n"
        "If you might act on these thoughts, call local emergency services now. In the "
        "U.S. or Canada, call or text 988. If you are elsewhere, contact your local "
        "crisis line or emergency number.\n\n"
        "## Safety disclaimer\n\n"
        "This is crisis safety guidance, not medical care."
    )


def harmful_fallback() -> str:
    return (
        "## Retrieved evidence\n\n"
        "I cannot help with instructions that could harm someone.\n\n"
        "## General explanation\n\n"
        "I can help reframe this toward safety, prevention, or how to get appropriate care.\n\n"
        "## Uncertainty\n\n"
        "I may not understand the full situation from a short message.\n\n"
        "## Recommended next step\n\n"
        "If there is immediate danger, contact local emergency services or a trusted "
        "person nearby.\n\n"
        "## Safety disclaimer\n\n"
        "This is safety information only."
    )


def validate_citations(citations: tuple[ProviderCitation, ...]) -> tuple[ProviderCitation, ...]:
    safe: list[ProviderCitation] = []
    for citation in citations:
        parsed = urlparse(citation.url)
        if parsed.scheme == "https" and parsed.hostname in TRUSTED_HOSTS:
            safe.append(citation)
    return tuple(safe)


def review_output(
    text: str,
    citations: tuple[ProviderCitation, ...],
    *,
    input_analysis: SafetyAnalysis,
    retrieval: RetrievalResult,
) -> SafetyReview:
    safe_citations = validate_citations(citations)
    categories = list(input_analysis.categories)
    action = input_analysis.action
    confidence = min(input_analysis.confidence, retrieval.top_score or input_analysis.confidence)
    if _matches(DIAGNOSIS_OUTPUT_PATTERNS, text):
        categories.append("diagnosis_language")
        text = re.sub(r"\byou have\b", "this can be associated with", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthis is definitely\b", "this may be", text, flags=re.IGNORECASE)
        action = "rewritten"
    if _matches(DOSAGE_OUTPUT_PATTERNS, text):
        categories.append("unsafe_dosage_language")
        text = medication_fallback()
        safe_citations = ()
        action = "fallback"
    if retrieval.no_answer and safe_citations:
        safe_citations = ()
    if (
        action != "fallback"
        and not safe_citations
        and not retrieval.no_answer
        and "## Retrieved evidence" in text
    ):
        categories.append("missing_citation")
        text = no_citation_fallback()
        action = "fallback"
    text = ensure_required_sections(text)
    if "pregnancy_child_caution" in categories and "pregnan" not in text.lower():
        text = text.replace(
            "## Recommended next step\n\n",
            "## Recommended next step\n\nFor pregnancy, infants, children, older adults, "
            "or complex conditions, contact a qualified clinician promptly. ",
            1,
        )
    return SafetyReview(
        text=text[:6000],
        citations=safe_citations,
        confidence=round(max(0.0, min(confidence, 1.0)), 4),
        categories=tuple(dict.fromkeys(categories)),
        action=action,
    )


def ensure_required_sections(text: str) -> str:
    if all(section in text for section in REQUIRED_SECTIONS):
        return text
    return (
        "## Retrieved evidence\n\n"
        "The safety engine could not verify the generated structure.\n\n"
        "## General explanation\n\n"
        f"{text}\n\n"
        "## Uncertainty\n\n"
        "Treat this as limited educational context.\n\n"
        "## Recommended next step\n\n"
        "Check with a qualified clinician or pharmacist for personal guidance.\n\n"
        "## Safety disclaimer\n\n"
        "This is educational information only, not a diagnosis or treatment plan."
    )


def medication_fallback() -> str:
    return (
        "## Retrieved evidence\n\n"
        "The safety engine removed medication-dosage language that was not appropriate "
        "to provide.\n\n"
        "## General explanation\n\n"
        "Medication dose decisions depend on age, weight, kidney or liver function, "
        "pregnancy status, other medicines, allergies, and the exact product.\n\n"
        "## Uncertainty\n\n"
        "I cannot verify those details here.\n\n"
        "## Recommended next step\n\n"
        "Ask a clinician or pharmacist, and follow the product label or prescription "
        "instructions.\n\n"
        "## Safety disclaimer\n\n"
        "This is medication safety information only, not dosing advice."
    )


def no_citation_fallback() -> str:
    return (
        "## Retrieved evidence\n\n"
        "I could not validate citations from approved sources for this answer.\n\n"
        "## General explanation\n\n"
        "I should not present medical claims without trusted evidence.\n\n"
        "## Uncertainty\n\n"
        "Confidence is low because citation validation failed.\n\n"
        "## Recommended next step\n\n"
        "Use a trusted public-health source or ask a qualified clinician.\n\n"
        "## Safety disclaimer\n\n"
        "This is educational information only, not a diagnosis or treatment plan."
    )


async def log_safety_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    conversation_id: uuid.UUID | None,
    message_id: uuid.UUID | None,
    stage: str,
    analysis: SafetyAnalysis | SafetyReview,
    text: str,
    metadata: dict[str, object] | None = None,
) -> None:
    db.add(
        SafetyEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            stage=stage,
            severity=getattr(analysis, "severity", "medium"),
            categories_json=list(analysis.categories),
            action=analysis.action,
            content_hash=content_hash(text),
            metadata_json=metadata or {},
            created_at=datetime.now(UTC),
        )
    )
