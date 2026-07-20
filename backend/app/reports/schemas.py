import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportAnalysisCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    record_id: uuid.UUID
    title: str | None = Field(default=None, max_length=220)


class ExtractedValue(BaseModel):
    label: str
    value: str
    unit: str | None
    reference_range: str | None
    flag: Literal["low", "normal", "high", "unknown"]
    confidence: float
    note: str


class ReportExplanation(BaseModel):
    summary: str
    ocr_uncertainty: str
    values: list[ExtractedValue]
    questions_for_doctor: list[str]
    disclaimer: str


class ReportAnalysisView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    profile_id: uuid.UUID
    record_id: uuid.UUID | None
    title: str
    status: str
    ocr_status: str
    ocr_confidence: float | None
    extracted_values_json: list[dict[str, object]]
    explanation_json: dict[str, object]
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
