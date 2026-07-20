import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.auth.models import User, UserRole
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.sharing.models import RecordShareGrant
from app.sharing.schemas import (
    AuditLogView,
    DoctorProfileCreate,
    DoctorProfileView,
    ReviewNoteCreate,
    ReviewNoteView,
    SharedRecordView,
    ShareGrantCreate,
    ShareGrantView,
)
from app.sharing.service import (
    create_review_note,
    create_share_grant,
    grant_record_ids,
    list_owner_grants,
    list_shared_records,
    owner_audit_logs,
    owner_review_notes,
    revoke_grant,
    upsert_doctor_profile,
    verified_doctors,
)

router = APIRouter()


async def grant_view(db: AsyncSession, grant: RecordShareGrant) -> ShareGrantView:
    return ShareGrantView(
        id=grant.id,
        owner_user_id=grant.owner_user_id,
        profile_id=grant.profile_id,
        doctor_user_id=grant.doctor_user_id,
        scope=grant.scope,
        note=grant.note,
        expires_at=grant.expires_at,
        revoked_at=grant.revoked_at,
        created_at=grant.created_at,
        record_ids=await grant_record_ids(db, grant.id),
    )


@router.post("/doctor/profile", response_model=ApiResponse[DoctorProfileView])
async def save_doctor_profile(
    payload: DoctorProfileCreate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(UserRole.DOCTOR)),
) -> ApiResponse[DoctorProfileView]:
    profile = await upsert_doctor_profile(db, doctor=user, payload=payload)
    await db.commit()
    return ApiResponse(data=DoctorProfileView.model_validate(profile))


@router.get("/doctors", response_model=ApiResponse[list[DoctorProfileView]])
async def doctors(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ApiResponse[list[DoctorProfileView]]:
    _ = user
    rows = await verified_doctors(db)
    return ApiResponse(data=[DoctorProfileView.model_validate(row) for row in rows])


@router.post("/grants", response_model=ApiResponse[ShareGrantView])
async def create_grant(
    payload: ShareGrantCreate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ApiResponse[ShareGrantView]:
    grant = await create_share_grant(db, owner=user, payload=payload)
    view = await grant_view(db, grant)
    await db.commit()
    return ApiResponse(data=view)


@router.get("/grants", response_model=ApiResponse[list[ShareGrantView]])
async def my_grants(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ApiResponse[list[ShareGrantView]]:
    grants = await list_owner_grants(db, owner=user)
    return ApiResponse(data=[await grant_view(db, grant) for grant in grants])


@router.post("/grants/{grant_id}/revoke", response_model=ApiResponse[ShareGrantView])
async def revoke(
    grant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ApiResponse[ShareGrantView]:
    grant = await revoke_grant(db, owner=user, grant_id=grant_id)
    view = await grant_view(db, grant)
    await db.commit()
    return ApiResponse(data=view)


@router.get("/doctor/records", response_model=ApiResponse[list[SharedRecordView]])
async def doctor_records(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(UserRole.DOCTOR)),
) -> ApiResponse[list[SharedRecordView]]:
    rows = await list_shared_records(db, doctor=user)
    return ApiResponse(
        data=[
            SharedRecordView(
                id=record.id,
                grant_id=grant.id,
                profile_id=record.profile_id,
                title=record.title,
                record_type=record.record_type,
                mime_type=record.mime_type,
                file_size_bytes=record.file_size_bytes,
                occurred_at=record.occurred_at,
                created_at=record.created_at,
                owner_user_id=record.owner_user_id,
            )
            for grant, record in rows
        ]
    )


@router.post(
    "/doctor/grants/{grant_id}/records/{record_id}/notes",
    response_model=ApiResponse[ReviewNoteView],
)
async def add_review_note(
    grant_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: ReviewNoteCreate,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_roles(UserRole.DOCTOR)),
) -> ApiResponse[ReviewNoteView]:
    note = await create_review_note(
        db, doctor=user, grant_id=grant_id, record_id=record_id, note=payload.note
    )
    await db.commit()
    return ApiResponse(data=ReviewNoteView.model_validate(note))


@router.get("/review-notes", response_model=ApiResponse[list[ReviewNoteView]])
async def my_review_notes(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ApiResponse[list[ReviewNoteView]]:
    rows = await owner_review_notes(db, owner=user)
    return ApiResponse(data=[ReviewNoteView.model_validate(row) for row in rows])


@router.get("/audit-logs", response_model=ApiResponse[list[AuditLogView]])
async def my_audit_logs(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ApiResponse[list[AuditLogView]]:
    rows = await owner_audit_logs(db, owner=user)
    return ApiResponse(data=[AuditLogView.model_validate(row) for row in rows])
