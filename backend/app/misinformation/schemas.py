import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Verdict = Literal[
    "likely_accurate",
    "misleading",
    "unsupported",
    "potentially_harmful",
    "insufficient_evidence",
]


class CheckCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    claim: str = Field(min_length=10, max_length=4000)

    @field_validator("claim")
    @classmethod
    def visible_claim(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Claim is required")
        return cleaned


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    rating: Literal["helpful", "not_helpful", "unsafe"]
    reason: str | None = Field(default=None, max_length=1000)


class CheckView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    claim_summary: str
    verdict: str
    evidence_json: dict[str, object]
    created_at: datetime
