import uuid

import pytest
from pydantic import ValidationError

from app.symptoms.schemas import SymptomAssessmentCreate
from app.symptoms.service import (
    cause_categories,
    doctor_questions,
    ensure_non_diagnostic,
    red_flags,
    safe_self_care,
    seek_care_text,
    urgency,
)


def payload(**overrides: object) -> SymptomAssessmentCreate:
    values: dict[str, object] = {
        "profile_id": uuid.uuid4(),
        "symptoms": ["fever", "cough"],
        "duration": "2 days",
        "severity": 5,
        "age_group": "adult",
        "relevant_context": "No known exposure",
        "associated_symptoms": ["sore throat"],
        "emergency_warning_signs": [],
    }
    values.update(overrides)
    return SymptomAssessmentCreate.model_validate(values)


def test_emergency_warning_signs_force_emergency_urgency() -> None:
    data = payload(
        symptoms=["chest pain"],
        severity=8,
        emergency_warning_signs=["cannot breathe"],
    )
    flags = red_flags(data)
    assert "Chest pain or pressure" in flags
    assert "Trouble breathing" in flags
    assert urgency(data, flags) == "emergency_now"
    assert "emergency services" in seek_care_text("emergency_now")


def test_high_risk_age_context_increases_caution() -> None:
    data = payload(symptoms=["fever"], severity=7, age_group="infant")
    flags = red_flags(data)
    assert "Higher-risk age or pregnancy context with significant symptoms" in flags
    assert urgency(data, flags) == "emergency_now"


def test_self_care_is_only_monitoring_level_and_cautious_for_children() -> None:
    mild = payload(symptoms=["mild headache"], duration="1 hour", severity=2, age_group="child")
    level = urgency(mild, red_flags(mild))
    care = safe_self_care(mild, level)
    assert level == "self_care_monitor"
    assert any("extra caution" in item for item in care)
    urgent = payload(symptoms=["vomiting"], duration="today", severity=8)
    assert safe_self_care(urgent, urgency(urgent, red_flags(urgent))) == [
        "Avoid delaying care to try home treatment first."
    ]


def test_possible_causes_are_categories_not_diagnoses() -> None:
    data = payload(symptoms=["rash", "itching"])
    categories = cause_categories(data)
    assert any("skin irritation" in category for category in categories)
    assert all("you have" not in category.lower() for category in categories)


@pytest.mark.parametrize(
    "unsafe",
    [
        "You have pneumonia.",
        "You definitely have the flu.",
        "This confirms appendicitis.",
    ],
)
def test_forbidden_diagnosis_phrases_are_removed(unsafe: str) -> None:
    result = ensure_non_diagnostic(unsafe)
    lowered = result.lower()
    assert "you have" not in lowered
    assert "you definitely have" not in lowered
    assert "this confirms" not in lowered


def test_doctor_questions_are_specific_without_claiming_diagnosis() -> None:
    questions = doctor_questions(payload(symptoms=["abdominal pain"]))
    assert len(questions) == 4
    assert any("warning signs" in question for question in questions)
    assert all("diagnosis is" not in question.lower() for question in questions)


def test_symptom_payload_validation_bounds_entries() -> None:
    with pytest.raises(ValidationError):
        SymptomAssessmentCreate(
            profile_id=uuid.uuid4(),
            symptoms=[],
            duration="today",
            severity=5,
            age_group="adult",
        )
    with pytest.raises(ValidationError):
        SymptomAssessmentCreate(
            profile_id=uuid.uuid4(),
            symptoms=["pain"],
            duration="today",
            severity=11,
            age_group="adult",
        )
