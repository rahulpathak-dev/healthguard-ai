import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.records.schemas import RecordAccess, RecordUpdate, RecordView
from app.records.service import (
    accessible_record,
    list_records,
    signed_access,
    update_record,
    upload_record,
)
from app.records.storage import storage

router = APIRouter()


@router.post("", response_model=ApiResponse[RecordView], status_code=201)
async def upload(
    profile_id: uuid.UUID = Form(),
    title: str = Form(min_length=1, max_length=220),
    record_type: str = Form(default="other", max_length=50),
    tags: str = Form(default=""),
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[RecordView]:
    record = await upload_record(
        db,
        user=user,
        profile_id=profile_id,
        title=title,
        record_type=record_type,
        file=file,
        tags=[item.strip() for item in tags.split(",") if item.strip()],
    )
    await db.commit()
    return ApiResponse(data=RecordView.model_validate(record))


@router.get("", response_model=ApiResponse[list[RecordView]])
async def records(
    profile_id: uuid.UUID,
    q: str | None = Query(default=None, max_length=80),
    record_type: str | None = Query(default=None, max_length=50),
    tag: str | None = Query(default=None, max_length=40),
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[RecordView]]:
    rows = await list_records(
        db,
        user_id=user.id,
        profile_id=profile_id,
        query=q,
        record_type=record_type,
        tag=tag,
        include_archived=include_archived,
    )
    return ApiResponse(data=[RecordView.model_validate(row) for row in rows])


@router.get("/files")
async def private_file(path: str, expires: int, signature: str) -> FileResponse:
    store = storage()
    if not store.validate_signature(path, expires, signature):
        raise HTTPException(status_code=403, detail="File link expired or invalid")
    target = store._resolve(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target, headers={"Cache-Control": "private, no-store"})


@router.get("/{record_id}", response_model=ApiResponse[RecordView])
async def detail(
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[RecordView]:
    record = await accessible_record(db, record_id=record_id, user_id=user.id)
    return ApiResponse(data=RecordView.model_validate(record))


@router.patch("/{record_id}", response_model=ApiResponse[RecordView])
async def update(
    record_id: uuid.UUID,
    payload: RecordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[RecordView]:
    record = await accessible_record(db, record_id=record_id, user_id=user.id, require_edit=True)
    await update_record(record, payload)
    await db.commit()
    return ApiResponse(data=RecordView.model_validate(record))


@router.post("/{record_id}/archive", response_model=ApiResponse[RecordView])
async def archive(
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[RecordView]:
    record = await accessible_record(db, record_id=record_id, user_id=user.id, require_edit=True)
    record.archived_at = datetime.now(UTC)
    record.status = "archived"
    await db.commit()
    return ApiResponse(data=RecordView.model_validate(record))


@router.delete("/{record_id}", status_code=204)
async def secure_delete(
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    record = await accessible_record(db, record_id=record_id, user_id=user.id, require_edit=True)
    await storage().delete(record.storage_path)
    record.deleted_at = datetime.now(UTC)
    record.status = "deleted"
    record.storage_path = ""
    await db.commit()


@router.post("/{record_id}/download-url", response_model=ApiResponse[RecordAccess])
async def download_url(
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[RecordAccess]:
    record = await accessible_record(db, record_id=record_id, user_id=user.id)
    preview_types = {"application/pdf", "image/png", "image/jpeg", "text/plain"}
    return ApiResponse(
        data=RecordAccess(
            url=signed_access(record),
            expires_in_seconds=300,
            preview_available=record.mime_type in preview_types,
        )
    )
