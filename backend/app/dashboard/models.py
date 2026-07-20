import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reminder(Base):
    __tablename__ = "health_reminders"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(40))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    recurrence_rule: Mapped[str] = mapped_column(String(24), default="none")
    status: Mapped[str] = mapped_column(String(24), default="pending")
    notes: Mapped[str | None] = mapped_column(String(500))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_health_reminders_profile_due", "profile_id", "status", "due_at"),
        Index("ix_health_reminders_owner_due", "owner_user_id", "status", "due_at"),
    )


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(220))
    record_type: Mapped[str] = mapped_column(String(50))
    original_filename: Mapped[str] = mapped_column(String(220), default="")
    mime_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(500), default="")
    sha256: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(24), default="quarantined", index=True)
    scan_status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_medical_records_profile_created", "profile_id", "created_at"),
        Index("ix_medical_records_profile_status", "profile_id", "status", "created_at"),
    )


class ReportAnalysis(Base):
    __tablename__ = "report_analyses"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_records.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(220))
    status: Mapped[str] = mapped_column(String(24))
    ocr_status: Mapped[str] = mapped_column(String(40), default="queued")
    ocr_confidence: Mapped[float | None] = mapped_column()
    extracted_values_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_report_analyses_profile_created", "profile_id", "created_at"),
        Index("ix_report_analyses_owner_created", "owner_user_id", "created_at"),
    )


class Conversation(Base):
    __tablename__ = "ai_conversations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(180))
    language: Mapped[str] = mapped_column(String(16), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_ai_conversations_profile_recent", "profile_id", "last_message_at"),)


class Notification(Base):
    __tablename__ = "user_notifications"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_user_notifications_unread", "user_id", "read_at", "created_at"),)
