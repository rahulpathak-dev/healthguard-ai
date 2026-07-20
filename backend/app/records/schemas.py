import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RecordCategory = Literal[
    "lab_report",
    "imaging",
    "prescription",
    "discharge_summary",
    "vaccination",
    "insurance",
    "other",
]


class RecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=220)
    record_type: RecordCategory | None = None
    occurred_at: datetime | None = None
    tags: list[str] | None = Field(default=None, max_length=12)
    metadata: dict[str, str] | None = None


class RecordView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    profile_id: uuid.UUID
    owner_user_id: uuid.UUID
    title: str
    record_type: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: str
    scan_status: str
    tags_json: list[str]
    metadata_json: dict[str, object]
    occurred_at: datetime | None
    created_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None


class RecordAccess(BaseModel):
    url: str
    expires_in_seconds: int
    preview_available: bool
