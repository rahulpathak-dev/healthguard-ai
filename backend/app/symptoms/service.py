import re
import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_safety.engine import analyze_input, log_safety_event
from app.auth.models import User
from app.core.config import get_settings
from app.rag.service import retrieve
from app.symptoms.models import SymptomAssessment
from app.symptoms.schemas import (
    SymptomAssessmentCreate,
    SymptomCitation,
    SymptomGuidance,
    UrgencyLevel,
)

EMERGENCY_TERMS = {
    "chest pain": "Chest pain or pressure",
    "cannot breathe": "Trouble breathing",
    "can't breathe": "Trouble breathing",
    "severe bleeding": "Severe bleeding",
    "unconscious": "Unconsciousness",
    "stroke": "Possible stroke signs",
    "face droop": "Possible stroke signs",
    "blue lips": "Blue lips or severe breathing difficulty",
    "stiff neck": "Severe headache or fever with stiff neck",
}
SOON_TERMS = {"fever", "pain", "vomiting", "dizzy", "rash", "cough", "shortness of breath"}
FORBIDDEN_DIAGNOSIS_PATTERNS = (
    r"\byou have\b",
    r"\byou definitely have\b",
    r"\bthis confirms\b",
)


def _joined(payload: SymptomAssessmentCreate) -> str:
    return " ".join(
        [
            *payload.symptoms,
            payload.duration,
            str(payload.severity),
            payload.age_group,
            payload.relevant_context or "",
            *payload.associated_symptoms,
            *payload.emergency_warning_signs,
        ]
    )


def red_flags(payload: SymptomAssessmentCreate) -> list[str]:
    text = _joined(payload).lower()
    findings = [
        label
        for term, label in EMERGENCY_TERMS.items()
        if term in text or any(term in sign.lower() for sign in payload.emergency_warning_signs)
    ]
    if payload.severity >= 9:
        findings.append("Very severe symptom intensity")
    if payload.age_group in {"infant", "pregnant"} and payload.severity >= 7:
        findings.append("Higher-risk age or pregnancy context with significant symptoms")
    return list(dict.fromkeys(findings))


def urgency(payload: SymptomAssessmentCreate, flags: list[str]) -> str:
    if flags:
        return "emergency_now"
    text = _joined(payload).lower()
    if payload.severity >= 7 or any(term in text for term in SOON_TERMS):
        return "urgent_today"
    if payload.severity >= 4 or "days" in payload.duration.lower():
        return "soon"
    return "self_care_monitor"


def cause_categories(payload: SymptomAssessmentCreate) -> list[str]:
    text = _joined(payload).lower()
    categories: list[str] = []
    if any(term in text for term in ("fever", "cough", "sore throat", "runny nose")):
        categories.append("infection-related or respiratory irritation patterns")
    if any(term in text for term in ("pain", "swelling", "injury", "strain")):
        categories.append("injury, inflammation, or strain-related patterns")
    if any(term in text for term in ("vomiting", "diarrhea", "nausea", "stomach")):
        categories.append("digestive irritation or fluid-loss related patterns")
    if any(term in text for term in ("rash", "itch", "allergy", "hives")):
        categories.append("skin irritation, allergy, or exposure-related patterns")
    if not categories:
        categories.append("common short-term, lifestyle, infection, or inflammation patterns")
    return categories


def safe_self_care(payload: SymptomAssessmentCreate, level: str) -> list[str]:
    if level in {"emergency_now", "urgent_today"}:
        return ["Avoid delaying care to try home treatment first."]
    care = [
        "Rest and avoid activities that clearly worsen the symptom.",
        "Drink fluids if you can do so safely.",
        "Track timing, severity, temperature, triggers, and new symptoms.",
    ]
    if payload.age_group in {"infant", "child", "pregnant", "older_adult"}:
        care.append("Use extra caution and ask a clinician before medicines or home remedies.")
    return care


def doctor_questions(payload: SymptomAssessmentCreate) -> list[str]:
    primary = ", ".join(payload.symptoms[:3])
    return [
        f"What details about {primary} would help decide whether an exam or test is needed?",
        "Which warning signs should prompt urgent care or emergency services?",
        "Could medicines, allergies, pregnancy, age, or chronic conditions change what to do next?",
        "What safe steps can be used at home, and what should be avoided?",
    ]


def ensure_non_diagnostic(text: str) -> str:
    result = text
    for pattern in FORBIDDEN_DIAGNOSIS_PATTERNS:
        result = re.sub(pattern, "this may be associated with", result, flags=re.IGNORECASE)
    return result


async def build_assessment(
    db: AsyncSession,
    *,
    user: User,
    payload: SymptomAssessmentCreate,
) -> SymptomAssessment:
    text = _joined(payload)
    analysis = analyze_input(text)
    flags = red_flags(payload)
    level = cast(UrgencyLevel, urgency(payload, flags))
    retrieval = await retrieve(db, query=text, user_id=user.id, conversation_id=None, limit=3)
    citations = [
        SymptomCitation(
            title=item.title,
            source=item.source,
            url=item.url,
            excerpt=item.excerpt,
        )
        for item in retrieval.evidence
    ]
    explanation = ensure_non_diagnostic(
        "This symptom flow provides general education only. It can help organize what is "
        "happening, identify warning signs, and prepare questions for a clinician. It does "
        "not diagnose, confirm, or rule out a condition."
    )
    guidance = SymptomGuidance(
        educational_explanation=explanation,
        possible_cause_categories=cause_categories(payload),
        urgency_level=level,
        red_flags=flags,
        when_to_seek_care=seek_care_text(level),
        doctor_questions=doctor_questions(payload),
        safe_self_care=safe_self_care(payload, level),
        disclaimer=get_settings().medical_disclaimer,
        citations=citations,
    )
    assessment = SymptomAssessment(
        profile_id=payload.profile_id,
        owner_user_id=user.id,
        symptoms_json=payload.symptoms,
        duration=payload.duration,
        severity=payload.severity,
        age_group=payload.age_group,
        relevant_context=payload.relevant_context,
        associated_symptoms_json=payload.associated_symptoms,
        warning_signs_json=payload.emergency_warning_signs,
        urgency_level=level,
        red_flags_json=flags,
        guidance_json=guidance.model_dump(mode="json"),
        created_at=datetime.now(UTC),
    )
    db.add(assessment)
    await log_safety_event(
        db,
        user_id=user.id,
        conversation_id=None,
        message_id=None,
        stage="symptom_input_analysis",
        analysis=analysis,
        text=text,
        metadata={"urgency_level": level, "red_flag_count": len(flags)},
    )
    await db.flush()
    return assessment


def seek_care_text(level: str) -> str:
    if level == "emergency_now":
        return "Seek emergency care now or call local emergency services."
    if level == "urgent_today":
        return "Contact a clinician, urgent care, or nurse advice line today."
    if level == "soon":
        return "Arrange non-urgent care if symptoms persist, worsen, or concern you."
    return "Monitor carefully and seek care if symptoms worsen or new warning signs appear."


async def owned_assessment(
    db: AsyncSession, assessment_id: uuid.UUID, user_id: uuid.UUID
) -> SymptomAssessment | None:
    return cast(
        SymptomAssessment | None,
        await db.scalar(
            select(SymptomAssessment).where(
                SymptomAssessment.id == assessment_id,
                SymptomAssessment.owner_user_id == user_id,
            )
        ),
    )
