import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import AdminAuditLog
from app.admin.schemas import AdminConfirmation, AdminOverview, PlatformConfiguration
from app.ai_safety.models import SafetyEvent
from app.auth.models import User
from app.chat.models import ChatMessage
from app.core.config import get_settings
from app.misinformation.models import MisinformationCheck
from app.rag.models import KnowledgeDocument, KnowledgeSource, RetrievalLog
from app.records.security import ALLOWED_TYPES
from app.reminders.models import ReminderDeliveryLog
from app.sharing.models import DoctorProfile


async def log_admin_action(
    db: AsyncSession,
    *,
    admin: User,
    action: str,
    target_type: str,
    target_id: str | None,
    reason: str,
    metadata: dict[str, object] | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            metadata_json=metadata or {},
            created_at=datetime.now(UTC),
        )
    )


def require_confirmation(payload: AdminConfirmation) -> None:
    if not payload.confirm:
        raise HTTPException(status_code=422, detail="Confirmation is required")


def email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else "redacted"


async def overview(db: AsyncSession) -> AdminOverview:
    users = await db.scalar(select(func.count()).select_from(User)) or 0
    active_users = (
        await db.scalar(select(func.count()).select_from(User).where(User.is_active)) or 0
    )
    doctors_pending = (
        await db.scalar(
            select(func.count())
            .select_from(DoctorProfile)
            .where(DoctorProfile.verification_status == "pending")
        )
        or 0
    )
    safety_events = await db.scalar(select(func.count()).select_from(SafetyEvent)) or 0
    misinformation = await db.scalar(select(func.count()).select_from(MisinformationCheck)) or 0
    approved_sources = (
        await db.scalar(
            select(func.count())
            .select_from(KnowledgeSource)
            .where(KnowledgeSource.approval_status == "approved")
        )
        or 0
    )
    notification_failures = (
        await db.scalar(
            select(func.count())
            .select_from(ReminderDeliveryLog)
            .where(ReminderDeliveryLog.status == "failed")
        )
        or 0
    )
    return AdminOverview(
        users=users,
        active_users=active_users,
        doctors_pending=doctors_pending,
        safety_events_open=safety_events,
        misinformation_checks=misinformation,
        approved_sources=approved_sources,
        notification_failures=notification_failures,
        system_health="ok",
        job_health="attention" if notification_failures else "ok",
    )


async def update_user_status(
    db: AsyncSession, *, admin: User, user_id: uuid.UUID, active: bool, reason: str
) -> User:
    if user_id == admin.id and not active:
        raise HTTPException(status_code=422, detail="Admins cannot disable their own account")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = active
    await log_admin_action(
        db,
        admin=admin,
        action="user_status_updated",
        target_type="user",
        target_id=str(user.id),
        reason=reason,
        metadata={"is_active": active},
    )
    return user


async def update_doctor_verification(
    db: AsyncSession, *, admin: User, doctor_id: uuid.UUID, status: str, reason: str
) -> DoctorProfile:
    profile = await db.get(DoctorProfile, doctor_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    profile.verification_status = status
    profile.verified_by = admin.id if status == "verified" else None
    profile.verified_at = datetime.now(UTC) if status == "verified" else None
    await log_admin_action(
        db,
        admin=admin,
        action="doctor_verification_updated",
        target_type="doctor_profile",
        target_id=str(profile.id),
        reason=reason,
        metadata={"verification_status": status},
    )
    return profile


async def update_source_status(
    db: AsyncSession, *, admin: User, source_id: uuid.UUID, status: str, reason: str
) -> KnowledgeSource:
    source = await db.get(KnowledgeSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    source.approval_status = status
    source.approved_by = admin.id if status == "approved" else None
    source.approved_at = datetime.now(UTC) if status == "approved" else None
    source.last_reviewed_at = datetime.now(UTC)
    await log_admin_action(
        db,
        admin=admin,
        action="knowledge_source_status_updated",
        target_type="knowledge_source",
        target_id=str(source.id),
        reason=reason,
        metadata={"approval_status": status},
    )
    return source


async def platform_config() -> PlatformConfiguration:
    settings = get_settings()
    return PlatformConfiguration(
        emergency_number_configured=bool(settings.emergency_number),
        storage_backend=settings.storage_backend,
        cookie_secure=settings.cookie_secure,
        allowed_record_types=sorted(ALLOWED_TYPES.keys()),
        source_ingestion_requires_approval=True,
    )


async def job_health(db: AsyncSession) -> dict[str, int | str]:
    docs = await db.scalar(select(func.count()).select_from(KnowledgeDocument)) or 0
    retrievals = await db.scalar(select(func.count()).select_from(RetrievalLog)) or 0
    failures = (
        await db.scalar(
            select(func.count())
            .select_from(ReminderDeliveryLog)
            .where(ReminderDeliveryLog.status == "failed")
        )
        or 0
    )
    return {
        "knowledge_documents": docs,
        "retrieval_logs": retrievals,
        "notification_failures": failures,
        "status": "attention" if failures else "ok",
    }


async def count_messages(db: AsyncSession, conversation_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
        )
        or 0
    )
