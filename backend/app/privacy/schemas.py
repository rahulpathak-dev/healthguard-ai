import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PrivacyPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cookie_preferences: dict[str, bool] = Field(default_factory=dict)
    notification_preferences: dict[str, bool] = Field(default_factory=dict)


class PrivacyPreferencesView(BaseModel):
    cookie_preferences_json: dict[str, object]
    notification_preferences_json: dict[str, object]
    updated_at: datetime


class ConsentEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    subject_type: str
    subject_id: str | None
    action: str
    metadata_json: dict[str, object]
    created_at: datetime


class ExportRequestView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_id: uuid.UUID | None
    status: str
    download_expires_at: datetime | None
    requested_at: datetime
    completed_at: datetime | None


class ExportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_ai_conversations: bool = True
    include_health_records_metadata: bool = True
    include_profiles: bool = True


class ExportDownload(BaseModel):
    url: str
    expires_at: datetime


class DeletionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    confirmation_phrase: str = Field(min_length=12, max_length=80)
    reason: str | None = Field(default=None, max_length=500)


class DeletionConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    confirmation_phrase: str = Field(min_length=12, max_length=80)


class DeletionRequestView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_id: uuid.UUID | None
    status: str
    grace_period_ends_at: datetime | None
    requested_at: datetime
    completed_at: datetime | None


class PrivacyCenterView(BaseModel):
    active_sessions: int
    active_sharing_grants: int
    consent_events: int
    pending_exports: int
    deletion_status: str | None
    retention_documentation: list[str]
    legal_compliance_note: str


PrivacyAction = Literal["ai_conversation_deleted", "health_record_deleted", "sharing_revoked"]
