import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SafetyReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message_id: uuid.UUID | None = None
    category: Literal[
        "unsafe_medical_advice",
        "missing_citation",
        "emergency_missed",
        "harmful_instruction",
        "privacy",
        "other",
    ]
    reason: str | None = Field(default=None, max_length=1000)


class SafetyReportView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    message_id: uuid.UUID | None
    category: str
    status: str
