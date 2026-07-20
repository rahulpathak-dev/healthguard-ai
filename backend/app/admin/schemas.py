import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DoctorVerification = Literal["pending", "verified", "rejected", "suspended"]
UserStatus = Literal["active", "disabled"]
SourceStatus = Literal["pending", "approved", "rejected", "retired"]


class AdminConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    confirm: bool
    reason: str = Field(min_length=3, max_length=500)


class UserStatusUpdate(AdminConfirmation):
    status: UserStatus


class DoctorVerificationUpdate(AdminConfirmation):
    verification_status: DoctorVerification


class SourceStatusUpdate(AdminConfirmation):
    approval_status: SourceStatus


class AdminOverview(BaseModel):
    users: int
    active_users: int
    doctors_pending: int
    safety_events_open: int
    misinformation_checks: int
    approved_sources: int
    notification_failures: int
    system_health: str
    job_health: str


class RedactedUserView(BaseModel):
    id: uuid.UUID
    email_domain: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime


class DoctorVerificationView(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    specialty: str | None
    license_region: str | None
    verification_status: str
    created_at: datetime


class SafetyEventReview(BaseModel):
    id: uuid.UUID
    severity: str
    stage: str
    action: str
    categories_json: list[str]
    created_at: datetime


class FlaggedConversationReview(BaseModel):
    id: uuid.UUID
    title: str
    language: str
    created_at: datetime
    last_message_at: datetime
    message_count: int
    content_redacted: bool = True


class MisinformationReview(BaseModel):
    id: uuid.UUID
    verdict: str
    claim_summary: str
    trusted_source_count: int
    created_at: datetime


class KnowledgeSourceReview(BaseModel):
    id: uuid.UUID
    name: str
    publisher: str
    base_url: str
    approval_status: str
    freshness_days: int
    last_reviewed_at: datetime | None
    created_at: datetime


class AdminAuditLogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    admin_user_id: uuid.UUID
    action: str
    target_type: str
    target_id: str | None
    reason: str | None
    metadata_json: dict[str, object]
    created_at: datetime


class PlatformConfiguration(BaseModel):
    emergency_number_configured: bool
    storage_backend: str
    cookie_secure: bool
    allowed_record_types: list[str]
    source_ingestion_requires_approval: bool = True
