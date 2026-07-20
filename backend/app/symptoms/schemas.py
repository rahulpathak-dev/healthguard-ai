import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AgeGroup = Literal["infant", "child", "teen", "adult", "older_adult", "pregnant"]
UrgencyLevel = Literal["emergency_now", "urgent_today", "soon", "self_care_monitor"]


class SymptomAssessmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    profile_id: uuid.UUID
    symptoms: list[str] = Field(min_length=1, max_length=8)
    duration: str = Field(min_length=1, max_length=120)
    severity: int = Field(ge=1, le=10)
    age_group: AgeGroup
    relevant_context: str | None = Field(default=None, max_length=1000)
    associated_symptoms: list[str] = Field(default_factory=list, max_length=12)
    emergency_warning_signs: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("symptoms", "associated_symptoms", "emergency_warning_signs")
    @classmethod
    def clean_items(cls, value: list[str]) -> list[str]:
        cleaned = [" ".join(item.split())[:120] for item in value if item and item.strip()]
        if not cleaned and value:
            raise ValueError("Entries must contain visible text")
        return cleaned


class SymptomCitation(BaseModel):
    title: str
    source: str
    url: str
    excerpt: str


class SymptomGuidance(BaseModel):
    educational_explanation: str
    possible_cause_categories: list[str]
    urgency_level: UrgencyLevel
    red_flags: list[str]
    when_to_seek_care: str
    doctor_questions: list[str]
    safe_self_care: list[str]
    disclaimer: str
    citations: list[SymptomCitation]


class SymptomAssessmentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    profile_id: uuid.UUID
    symptoms_json: list[str]
    duration: str
    severity: int
    age_group: str
    urgency_level: str
    red_flags_json: list[str]
    guidance_json: dict[str, object]
    created_at: datetime
