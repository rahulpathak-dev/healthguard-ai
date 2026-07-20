import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dashboard.models import MedicalRecord
from app.profiles.models import HealthProfile, PermissionLevel, ProfilePermission
from app.profiles.service import get_accessible_profile
from app.records.schemas import RecordUpdate
from app.records.security import metadata_safe_tags, validate_file
from app.records.storage import storage


async def upload_record(
    db: AsyncSession,
    *,
    user: User,
    profile_id: uuid.UUID,
    title: str,
    record_type: str,
    file: UploadFile,
    tags: list[str],
) -> MedicalRecord:
    await get_accessible_profile(db, profile_id, user.id, require_edit=True)
    data = await file.read()
    validation = validate_file(file.filename or "", file.content_type or "", data)
    record = MedicalRecord(
        profile_id=profile_id,
        owner_user_id=user.id,
        title=title,
        record_type=record_type,
        occurred_at=None,
        original_filename=validation.safe_filename,
        mime_type=validation.mime_type,
        file_size_bytes=validation.size_bytes,
        storage_path="pending",
        sha256="pending",
        status="quarantined",
        scan_status="pending",
        tags_json=metadata_safe_tags(tags),
        metadata_json={"malware_scanning": "pending"},
        created_at=datetime.now(UTC),
    )
    db.add(record)
    await db.flush()
    stored = await storage().put_quarantine(
        record_id=record.id, extension=validation.extension, data=data
    )
    record.storage_path = stored.storage_path
    record.sha256 = stored.sha256
    return record


async def accessible_record(
    db: AsyncSession, *, record_id: uuid.UUID, user_id: uuid.UUID, require_edit: bool = False
) -> MedicalRecord:
    permission = ProfilePermission
    row = await db.scalar(
        select(MedicalRecord)
        .join(HealthProfile, HealthProfile.id == MedicalRecord.profile_id)
        .outerjoin(
            permission,
            (permission.profile_id == HealthProfile.id) & (permission.grantee_user_id == user_id),
        )
        .where(
            MedicalRecord.id == record_id,
            MedicalRecord.deleted_at.is_(None),
            or_(HealthProfile.owner_user_id == user_id, permission.grantee_user_id == user_id),
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if require_edit and row.owner_user_id != user_id:
        profile = await db.get(HealthProfile, row.profile_id)
        granted = await db.scalar(
            select(ProfilePermission).where(
                ProfilePermission.profile_id == row.profile_id,
                ProfilePermission.grantee_user_id == user_id,
                ProfilePermission.level == PermissionLevel.EDIT,
            )
        )
        if profile is None or (profile.owner_user_id != user_id and granted is None):
            raise HTTPException(status_code=404, detail="Record not found")
    return row


async def list_records(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    profile_id: uuid.UUID,
    query: str | None,
    record_type: str | None,
    tag: str | None,
    include_archived: bool,
) -> list[MedicalRecord]:
    await get_accessible_profile(db, profile_id, user_id)
    statement = select(MedicalRecord).where(
        MedicalRecord.profile_id == profile_id,
        MedicalRecord.deleted_at.is_(None),
    )
    if not include_archived:
        statement = statement.where(MedicalRecord.archived_at.is_(None))
    if query:
        statement = statement.where(MedicalRecord.title.ilike(f"%{query[:80]}%"))
    if record_type:
        statement = statement.where(MedicalRecord.record_type == record_type)
    if tag:
        statement = statement.where(MedicalRecord.tags_json.contains([tag.lower()]))
    rows = (await db.scalars(statement.order_by(MedicalRecord.created_at.desc()).limit(100))).all()
    return list(rows)


def signed_access(record: MedicalRecord) -> str:
    if record.status != "available" or record.scan_status != "clean":
        raise HTTPException(status_code=409, detail="Record file is not available")
    return storage().signed_url(record.storage_path)


async def update_record(record: MedicalRecord, payload: RecordUpdate) -> MedicalRecord:
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes and payload.title:
        record.title = payload.title
    if "record_type" in changes and payload.record_type:
        record.record_type = payload.record_type
    if "occurred_at" in changes:
        record.occurred_at = payload.occurred_at
    if payload.tags is not None:
        record.tags_json = metadata_safe_tags(payload.tags)
    if payload.metadata is not None:
        record.metadata_json = {key[:40]: value[:160] for key, value in payload.metadata.items()}
    return record
