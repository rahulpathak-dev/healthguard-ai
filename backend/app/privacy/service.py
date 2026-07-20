import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Session, User
from app.auth.security import digest_token
from app.auth.service import revoke_all_sessions
from app.chat.models import ChatMessage
from app.dashboard.models import Conversation, MedicalRecord
from app.jobs.service import enqueue_job, mark_completed, mark_started
from app.privacy.models import (
    AccountDeletionRequest,
    ConsentEvent,
    DataExportRequest,
    PrivacyPreference,
)
from app.privacy.schemas import (
    DeletionCreate,
    ExportCreate,
    PrivacyCenterView,
    PrivacyPreferencesUpdate,
)
from app.profiles.models import HealthProfile
from app.records.storage import storage
from app.sharing.models import RecordShareGrant

EXPORT_ROOT = Path(".local/exports")
DELETE_PHRASE = "delete my healthguard account"


def now() -> datetime:
    return datetime.now(UTC)


async def record_consent_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    event_type: str,
    subject_type: str,
    action: str,
    subject_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> ConsentEvent:
    event = ConsentEvent(
        user_id=user_id,
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        action=action,
        metadata_json=metadata or {},
        created_at=now(),
    )
    db.add(event)
    return event


async def privacy_center(db: AsyncSession, user: User) -> PrivacyCenterView:
    active_sessions = (
        await db.scalar(
            select(func.count())
            .select_from(Session)
            .where(
                Session.user_id == user.id,
                Session.revoked_at.is_(None),
                Session.expires_at > now(),
            )
        )
        or 0
    )
    active_grants = (
        await db.scalar(
            select(func.count())
            .select_from(RecordShareGrant)
            .where(
                RecordShareGrant.owner_user_id == user.id,
                RecordShareGrant.revoked_at.is_(None),
                RecordShareGrant.expires_at > now(),
            )
        )
        or 0
    )
    events = (
        await db.scalar(
            select(func.count()).select_from(ConsentEvent).where(ConsentEvent.user_id == user.id)
        )
        or 0
    )
    exports = (
        await db.scalar(
            select(func.count())
            .select_from(DataExportRequest)
            .where(
                DataExportRequest.user_id == user.id,
                DataExportRequest.status.in_(["queued", "running", "ready"]),
            )
        )
        or 0
    )
    deletion = await db.scalar(
        select(AccountDeletionRequest)
        .where(AccountDeletionRequest.user_id == user.id)
        .order_by(AccountDeletionRequest.requested_at.desc())
        .limit(1)
    )
    return PrivacyCenterView(
        active_sessions=active_sessions,
        active_sharing_grants=active_grants,
        consent_events=events,
        pending_exports=exports,
        deletion_status=deletion.status if deletion else None,
        retention_documentation=[
            "Medical record files are deleted from private storage when records are "
            "securely deleted.",
            "Refresh sessions are revoked during password reset, logout-all, and "
            "confirmed deletion.",
            "Audit logs are retained for security evidence and minimize medical content.",
            "Exports use short-lived download tokens and private no-store responses.",
        ],
        legal_compliance_note=(
            "HealthGuard AI uses privacy-by-design controls; this product does not claim "
            "automatic legal compliance."
        ),
    )


async def get_preferences(db: AsyncSession, user: User) -> PrivacyPreference:
    pref = await db.scalar(select(PrivacyPreference).where(PrivacyPreference.user_id == user.id))
    if pref:
        return pref
    pref = PrivacyPreference(
        user_id=user.id,
        cookie_preferences_json={"essential": True, "analytics": False},
        notification_preferences_json={"email": True, "sms": False, "push": False},
        updated_at=now(),
    )
    db.add(pref)
    await db.flush()
    return pref


async def update_preferences(
    db: AsyncSession, user: User, payload: PrivacyPreferencesUpdate
) -> PrivacyPreference:
    pref = await get_preferences(db, user)
    pref.cookie_preferences_json = cast(
        dict[str, object], dict(payload.cookie_preferences) | {"essential": True}
    )
    pref.notification_preferences_json = cast(
        dict[str, object], dict(payload.notification_preferences)
    )
    pref.updated_at = now()
    await record_consent_event(
        db,
        user_id=user.id,
        event_type="preference_update",
        subject_type="privacy_preferences",
        action="updated",
    )
    return pref


async def create_export(db: AsyncSession, user: User, payload: ExportCreate) -> DataExportRequest:
    job = await enqueue_job(
        db,
        job_type="privacy_export",
        payload=payload.model_dump(),
        queue="privacy",
        owner_user_id=user.id,
        idempotency_key=f"privacy-export:{user.id}:{int(now().timestamp())}",
    )
    request = DataExportRequest(
        user_id=user.id, job_id=job.id, status="running", requested_at=now()
    )
    db.add(request)
    await db.flush()
    await mark_started(job)
    data: dict[str, object] = {"generated_at": now().isoformat(), "user_id": str(user.id)}
    if payload.include_profiles:
        profiles = (
            await db.scalars(select(HealthProfile).where(HealthProfile.owner_user_id == user.id))
        ).all()
        data["profiles"] = [
            {"id": str(row.id), "display_name": row.display_name, "kind": row.kind.value}
            for row in profiles
        ]
    if payload.include_health_records_metadata:
        records = (
            await db.scalars(select(MedicalRecord).where(MedicalRecord.owner_user_id == user.id))
        ).all()
        data["record_metadata"] = [
            {"id": str(row.id), "title": row.title, "type": row.record_type, "status": row.status}
            for row in records
        ]
    if payload.include_ai_conversations:
        conversations = (
            await db.scalars(select(Conversation).where(Conversation.owner_user_id == user.id))
        ).all()
        data["ai_conversations"] = [
            {"id": str(row.id), "title": row.title, "created_at": row.created_at.isoformat()}
            for row in conversations
        ]
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    path = EXPORT_ROOT / f"export-{request.id}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    request.export_path = str(path)
    request.download_token_hash = digest_token(token)
    request.download_expires_at = now() + timedelta(minutes=15)
    request.status = "ready"
    request.completed_at = now()
    request.metadata_token = token  # type: ignore[attr-defined]
    await mark_completed(job)
    await record_consent_event(
        db,
        user_id=user.id,
        event_type="data_export",
        subject_type="account",
        action="created",
        subject_id=str(request.id),
    )
    return request


async def export_download_token(
    db: AsyncSession, user: User, export_id: uuid.UUID
) -> tuple[DataExportRequest, str]:
    request = await db.get(DataExportRequest, export_id)
    if request is None or request.user_id != user.id or request.status != "ready":
        raise HTTPException(status_code=404, detail="Export not found")
    token = secrets.token_urlsafe(32)
    request.download_token_hash = digest_token(token)
    request.download_expires_at = now() + timedelta(minutes=10)
    return request, token


async def validate_export_token(
    db: AsyncSession, export_id: uuid.UUID, token: str
) -> DataExportRequest:
    request = await db.get(DataExportRequest, export_id)
    if (
        request is None
        or request.download_token_hash != digest_token(token)
        or request.download_expires_at is None
        or request.download_expires_at <= now()
        or not request.export_path
    ):
        raise HTTPException(status_code=403, detail="Export link expired or invalid")
    return request


async def create_deletion_request(
    db: AsyncSession, user: User, payload: DeletionCreate, grace_days: int
) -> AccountDeletionRequest:
    if payload.confirmation_phrase.lower() != DELETE_PHRASE:
        raise HTTPException(status_code=422, detail="Confirmation phrase did not match")
    request = AccountDeletionRequest(
        user_id=user.id,
        status="pending" if grace_days else "ready",
        confirmation_phrase_hash=digest_token(payload.confirmation_phrase.lower()),
        grace_period_ends_at=now() + timedelta(days=grace_days) if grace_days else None,
        requested_at=now(),
        reason=payload.reason,
    )
    db.add(request)
    await revoke_all_sessions(db, user.id)
    await record_consent_event(
        db,
        user_id=user.id,
        event_type="account_deletion",
        subject_type="account",
        action="requested",
    )
    return request


async def confirm_deletion(
    db: AsyncSession, user: User, request_id: uuid.UUID, phrase: str
) -> AccountDeletionRequest:
    request = await db.get(AccountDeletionRequest, request_id)
    if request is None or request.user_id != user.id:
        raise HTTPException(status_code=404, detail="Deletion request not found")
    if request.confirmation_phrase_hash != digest_token(phrase.lower()):
        raise HTTPException(status_code=422, detail="Confirmation phrase did not match")
    if request.grace_period_ends_at and request.grace_period_ends_at > now():
        raise HTTPException(status_code=409, detail="Deletion grace period has not ended")
    job = await enqueue_job(
        db,
        job_type="account_deletion",
        payload={"user_id": str(user.id)},
        queue="privacy",
        owner_user_id=user.id,
        idempotency_key=f"account-deletion:{request.id}",
        max_attempts=1,
    )
    request.job_id = job.id
    await mark_started(job)
    records = (
        await db.scalars(select(MedicalRecord).where(MedicalRecord.owner_user_id == user.id))
    ).all()
    for record in records:
        if record.storage_path:
            await storage().delete(record.storage_path)
        record.deleted_at = now()
        record.status = "deleted"
        record.storage_path = ""
    await db.execute(
        delete(ChatMessage).where(
            ChatMessage.conversation_id.in_(
                select(Conversation.id).where(Conversation.owner_user_id == user.id)
            )
        )
    )
    await db.execute(delete(Conversation).where(Conversation.owner_user_id == user.id))
    await db.execute(delete(RecordShareGrant).where(RecordShareGrant.owner_user_id == user.id))
    await revoke_all_sessions(db, user.id)
    user.is_active = False
    request.status = "completed"
    request.completed_at = now()
    await mark_completed(job)
    await record_consent_event(
        db,
        user_id=user.id,
        event_type="account_deletion",
        subject_type="account",
        action="completed",
    )
    return request
