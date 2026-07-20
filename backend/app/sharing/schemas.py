import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PermissionScope = Literal["read"]
VerificationStatus = Literal["pending", "verified", "rejected", "suspended"]


class DoctorProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str = Field(min_length=2, max_length=160)
    specialty: str | None = Field(default=None, max_length=120)
    license_region: str | None = Field(default=None, max_length=80)


class DoctorProfileView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    specialty: str | None
    license_region: str | None
    verification_status: str
    verified_at: datetime | None
    created_at: datetime


class ShareGrantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    profile_id: uuid.UUID
    doctor_user_id: uuid.UUID
    record_ids: list[uuid.UUID] = Field(min_length=1, max_length=25)
    expires_at: datetime
    scope: PermissionScope = "read"
    note: str | None = Field(default=None, max_length=300)

    @field_validator("record_ids")
    @classmethod
    def unique_records(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Duplicate records are not allowed")
        return value


class ShareGrantView(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    profile_id: uuid.UUID
    doctor_user_id: uuid.UUID
    scope: str
    note: str | None
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    record_ids: list[uuid.UUID]


class SharedRecordView(BaseModel):
    id: uuid.UUID
    grant_id: uuid.UUID
    profile_id: uuid.UUID
    title: str
    record_type: str
    mime_type: str
    file_size_bytes: int
    occurred_at: datetime | None
    created_at: datetime
    owner_user_id: uuid.UUID


class ReviewNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    note: str = Field(min_length=2, max_length=5000)


class ReviewNoteView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    grant_id: uuid.UUID
    record_id: uuid.UUID
    doctor_user_id: uuid.UUID
    owner_user_id: uuid.UUID
    note: str
    created_at: datetime


class AuditLogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    actor_user_id: uuid.UUID
    owner_user_id: uuid.UUID
    grant_id: uuid.UUID | None
    record_id: uuid.UUID | None
    action: str
    metadata_json: dict[str, object]
    created_at: datetime
