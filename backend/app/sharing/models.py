import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(160))
    specialty: Mapped[str | None] = mapped_column(String(120))
    license_region: Mapped[str | None] = mapped_column(String(80))
    verification_status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RecordShareGrant(Base):
    __tablename__ = "record_share_grants"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    doctor_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[str] = mapped_column(String(24), default="read")
    note: Mapped[str | None] = mapped_column(String(300))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_record_share_grants_owner_created", "owner_user_id", "created_at"),
        Index("ix_record_share_grants_doctor_active", "doctor_user_id", "revoked_at", "expires_at"),
    )


class RecordShareGrantItem(Base):
    __tablename__ = "record_share_grant_items"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    grant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("record_share_grants.id", ondelete="CASCADE"), index=True
    )
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medical_records.id", ondelete="CASCADE"), index=True
    )
    __table_args__ = (Index("uq_grant_record", "grant_id", "record_id", unique=True),)


class DoctorReviewNote(Base):
    __tablename__ = "doctor_review_notes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    grant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("record_share_grants.id", ondelete="CASCADE"), index=True
    )
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medical_records.id", ondelete="CASCADE"), index=True
    )
    doctor_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RecordAccessAuditLog(Base):
    __tablename__ = "record_access_audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    grant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("record_share_grants.id", ondelete="SET NULL"), index=True
    )
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_records.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(40), index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
