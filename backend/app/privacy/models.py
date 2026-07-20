import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConsentEvent(Base):
    __tablename__ = "consent_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(60), index=True)
    subject_type: Mapped[str] = mapped_column(String(60))
    subject_id: Mapped[str | None] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(60), index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = (Index("ix_consent_events_user_created", "user_id", "created_at"),)


class DataExportRequest(Base):
    __tablename__ = "data_export_requests"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("background_jobs.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    export_path: Mapped[str | None] = mapped_column(String(500))
    download_token_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    download_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("background_jobs.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    confirmation_phrase_hash: Mapped[str] = mapped_column(String(64))
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(Text)


class PrivacyPreference(Base):
    __tablename__ = "privacy_preferences"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    cookie_preferences_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    notification_preferences_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
