import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.dashboard.models import MedicalRecord
from app.profiles.service import get_accessible_profile
from app.sharing.models import (
    DoctorProfile,
    DoctorReviewNote,
    RecordAccessAuditLog,
    RecordShareGrant,
    RecordShareGrantItem,
)
from app.sharing.schemas import DoctorProfileCreate, ShareGrantCreate


async def audit(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    action: str,
    grant_id: uuid.UUID | None = None,
    record_id: uuid.UUID | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    db.add(
        RecordAccessAuditLog(
            actor_user_id=actor_user_id,
            owner_user_id=owner_user_id,
            grant_id=grant_id,
            record_id=record_id,
            action=action,
            metadata_json=metadata or {},
            created_at=datetime.now(UTC),
        )
    )


async def upsert_doctor_profile(
    db: AsyncSession, *, doctor: User, payload: DoctorProfileCreate
) -> DoctorProfile:
    if doctor.role != UserRole.DOCTOR:
        raise HTTPException(status_code=403, detail="Doctor role required")
    existing = await db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == doctor.id))
    now = datetime.now(UTC)
    if existing:
        existing.display_name = payload.display_name
        existing.specialty = payload.specialty
        existing.license_region = payload.license_region
        return existing
    profile = DoctorProfile(
        user_id=doctor.id,
        display_name=payload.display_name,
        specialty=payload.specialty,
        license_region=payload.license_region,
        verification_status="pending",
        created_at=now,
    )
    db.add(profile)
    await db.flush()
    return profile


async def create_share_grant(
    db: AsyncSession, *, owner: User, payload: ShareGrantCreate
) -> RecordShareGrant:
    now = datetime.now(UTC)
    if payload.expires_at <= now:
        raise HTTPException(status_code=422, detail="Expiry must be in the future")
    doctor = await db.get(User, payload.doctor_user_id)
    if doctor is None or doctor.role != UserRole.DOCTOR or not doctor.is_active:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor_profile = await db.scalar(
        select(DoctorProfile).where(DoctorProfile.user_id == payload.doctor_user_id)
    )
    if doctor_profile is None or doctor_profile.verification_status != "verified":
        raise HTTPException(status_code=409, detail="Doctor is not verified")
    await get_accessible_profile(db, payload.profile_id, owner.id, require_edit=True)
    records = (
        await db.scalars(
            select(MedicalRecord).where(
                MedicalRecord.id.in_(payload.record_ids),
                MedicalRecord.profile_id == payload.profile_id,
                MedicalRecord.owner_user_id == owner.id,
                MedicalRecord.deleted_at.is_(None),
            )
        )
    ).all()
    if len(records) != len(payload.record_ids):
        raise HTTPException(status_code=404, detail="One or more records were not found")
    grant = RecordShareGrant(
        owner_user_id=owner.id,
        profile_id=payload.profile_id,
        doctor_user_id=payload.doctor_user_id,
        scope="read",
        note=payload.note,
        expires_at=payload.expires_at,
        created_at=now,
    )
    db.add(grant)
    await db.flush()
    for record_id in payload.record_ids:
        db.add(RecordShareGrantItem(grant_id=grant.id, record_id=record_id))
    await audit(
        db,
        actor_user_id=owner.id,
        owner_user_id=owner.id,
        action="grant_created",
        grant_id=grant.id,
        metadata={"record_count": len(payload.record_ids), "scope": "read"},
    )
    return grant


async def grant_record_ids(db: AsyncSession, grant_id: uuid.UUID) -> list[uuid.UUID]:
    rows = (
        await db.scalars(
            select(RecordShareGrantItem.record_id).where(RecordShareGrantItem.grant_id == grant_id)
        )
    ).all()
    return list(rows)


async def list_owner_grants(db: AsyncSession, *, owner: User) -> list[RecordShareGrant]:
    rows = (
        await db.scalars(
            select(RecordShareGrant)
            .where(RecordShareGrant.owner_user_id == owner.id)
            .order_by(RecordShareGrant.created_at.desc())
            .limit(100)
        )
    ).all()
    return list(rows)


async def revoke_grant(db: AsyncSession, *, owner: User, grant_id: uuid.UUID) -> RecordShareGrant:
    grant = await db.get(RecordShareGrant, grant_id)
    if grant is None or grant.owner_user_id != owner.id:
        raise HTTPException(status_code=404, detail="Grant not found")
    if grant.revoked_at is None:
        grant.revoked_at = datetime.now(UTC)
        await audit(
            db,
            actor_user_id=owner.id,
            owner_user_id=owner.id,
            action="grant_revoked",
            grant_id=grant.id,
        )
    return grant


async def active_grant_for_record(
    db: AsyncSession, *, doctor: User, grant_id: uuid.UUID, record_id: uuid.UUID
) -> tuple[RecordShareGrant, MedicalRecord]:
    now = datetime.now(UTC)
    row = await db.execute(
        select(RecordShareGrant, MedicalRecord)
        .join(RecordShareGrantItem, RecordShareGrantItem.grant_id == RecordShareGrant.id)
        .join(MedicalRecord, MedicalRecord.id == RecordShareGrantItem.record_id)
        .where(
            RecordShareGrant.id == grant_id,
            RecordShareGrant.doctor_user_id == doctor.id,
            RecordShareGrant.revoked_at.is_(None),
            RecordShareGrant.expires_at > now,
            RecordShareGrantItem.record_id == record_id,
            MedicalRecord.deleted_at.is_(None),
        )
    )
    result = row.first()
    if result is None:
        raise HTTPException(status_code=404, detail="Shared record not found")
    grant, record = result.tuple()
    await audit(
        db,
        actor_user_id=doctor.id,
        owner_user_id=grant.owner_user_id,
        action="record_viewed",
        grant_id=grant.id,
        record_id=record.id,
    )
    return grant, record


async def list_shared_records(
    db: AsyncSession, *, doctor: User
) -> list[tuple[RecordShareGrant, MedicalRecord]]:
    now = datetime.now(UTC)
    rows = await db.execute(
        select(RecordShareGrant, MedicalRecord)
        .join(RecordShareGrantItem, RecordShareGrantItem.grant_id == RecordShareGrant.id)
        .join(MedicalRecord, MedicalRecord.id == RecordShareGrantItem.record_id)
        .where(
            RecordShareGrant.doctor_user_id == doctor.id,
            RecordShareGrant.revoked_at.is_(None),
            RecordShareGrant.expires_at > now,
            MedicalRecord.deleted_at.is_(None),
        )
        .order_by(RecordShareGrant.expires_at.asc(), MedicalRecord.created_at.desc())
        .limit(100)
    )
    return [(grant, record) for grant, record in rows.tuples()]


async def create_review_note(
    db: AsyncSession, *, doctor: User, grant_id: uuid.UUID, record_id: uuid.UUID, note: str
) -> DoctorReviewNote:
    grant, record = await active_grant_for_record(
        db, doctor=doctor, grant_id=grant_id, record_id=record_id
    )
    review = DoctorReviewNote(
        grant_id=grant.id,
        record_id=record.id,
        doctor_user_id=doctor.id,
        owner_user_id=grant.owner_user_id,
        note=note,
        created_at=datetime.now(UTC),
    )
    db.add(review)
    await audit(
        db,
        actor_user_id=doctor.id,
        owner_user_id=grant.owner_user_id,
        action="review_note_created",
        grant_id=grant.id,
        record_id=record.id,
    )
    return review


async def owner_review_notes(db: AsyncSession, *, owner: User) -> list[DoctorReviewNote]:
    rows = (
        await db.scalars(
            select(DoctorReviewNote)
            .where(DoctorReviewNote.owner_user_id == owner.id)
            .order_by(DoctorReviewNote.created_at.desc())
            .limit(100)
        )
    ).all()
    return list(rows)


async def owner_audit_logs(db: AsyncSession, *, owner: User) -> list[RecordAccessAuditLog]:
    rows = (
        await db.scalars(
            select(RecordAccessAuditLog)
            .where(RecordAccessAuditLog.owner_user_id == owner.id)
            .order_by(RecordAccessAuditLog.created_at.desc())
            .limit(100)
        )
    ).all()
    return list(rows)


async def verified_doctors(db: AsyncSession) -> list[DoctorProfile]:
    rows = (
        await db.scalars(
            select(DoctorProfile)
            .where(DoctorProfile.verification_status == "verified")
            .order_by(DoctorProfile.display_name.asc())
            .limit(100)
        )
    ).all()
    return list(rows)


def share_is_active(grant: RecordShareGrant) -> bool:
    return grant.revoked_at is None and grant.expires_at > datetime.now(UTC)
