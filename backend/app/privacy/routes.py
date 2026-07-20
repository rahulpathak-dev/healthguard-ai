import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import get_settings
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.privacy.models import AccountDeletionRequest, ConsentEvent, DataExportRequest
from app.privacy.schemas import (
    ConsentEventView,
    DeletionConfirm,
    DeletionCreate,
    DeletionRequestView,
    ExportCreate,
    ExportDownload,
    ExportRequestView,
    PrivacyCenterView,
    PrivacyPreferencesUpdate,
    PrivacyPreferencesView,
)
from app.privacy.service import (
    confirm_deletion,
    create_deletion_request,
    create_export,
    export_download_token,
    get_preferences,
    privacy_center,
    update_preferences,
    validate_export_token,
)

router = APIRouter()


@router.get("/center", response_model=ApiResponse[PrivacyCenterView])
async def center(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[PrivacyCenterView]:
    return ApiResponse(data=await privacy_center(db, user))


@router.get("/preferences", response_model=ApiResponse[PrivacyPreferencesView])
async def preferences(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[PrivacyPreferencesView]:
    pref = await get_preferences(db, user)
    await db.commit()
    return ApiResponse(data=PrivacyPreferencesView.model_validate(pref, from_attributes=True))


@router.put("/preferences", response_model=ApiResponse[PrivacyPreferencesView])
async def save_preferences(
    payload: PrivacyPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[PrivacyPreferencesView]:
    pref = await update_preferences(db, user, payload)
    await db.commit()
    return ApiResponse(data=PrivacyPreferencesView.model_validate(pref, from_attributes=True))


@router.get("/consent-history", response_model=ApiResponse[list[ConsentEventView]])
async def consent_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[list[ConsentEventView]]:
    rows = (
        await db.scalars(
            select(ConsentEvent)
            .where(ConsentEvent.user_id == user.id)
            .order_by(ConsentEvent.created_at.desc())
            .limit(100)
        )
    ).all()
    return ApiResponse(data=[ConsentEventView.model_validate(row) for row in rows])


@router.post("/exports", response_model=ApiResponse[ExportRequestView], status_code=202)
async def request_export(
    payload: ExportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ExportRequestView]:
    export = await create_export(db, user, payload)
    await db.commit()
    return ApiResponse(data=ExportRequestView.model_validate(export))


@router.get("/exports", response_model=ApiResponse[list[ExportRequestView]])
async def exports(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[list[ExportRequestView]]:
    rows = (
        await db.scalars(
            select(DataExportRequest)
            .where(DataExportRequest.user_id == user.id)
            .order_by(DataExportRequest.requested_at.desc())
            .limit(25)
        )
    ).all()
    return ApiResponse(data=[ExportRequestView.model_validate(row) for row in rows])


@router.post("/exports/{export_id}/download", response_model=ApiResponse[ExportDownload])
async def export_download(
    export_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ExportDownload]:
    export, token = await export_download_token(db, user, export_id)
    if export.download_expires_at is None:
        raise HTTPException(status_code=409, detail="Export is not ready for download")
    await db.commit()
    return ApiResponse(
        data=ExportDownload(
            url=f"/api/v1/privacy/exports/{export.id}/file?token={token}",
            expires_at=export.download_expires_at,
        )
    )


@router.get("/exports/{export_id}/file")
async def export_file(
    export_id: uuid.UUID, token: str, db: AsyncSession = Depends(get_db_session)
) -> FileResponse:
    export = await validate_export_token(db, export_id, token)
    path = Path(export.export_path or "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file is no longer available")
    return FileResponse(
        path, media_type="application/json", headers={"Cache-Control": "private, no-store"}
    )


@router.post("/deletion", response_model=ApiResponse[DeletionRequestView], status_code=202)
async def deletion_request(
    payload: DeletionCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DeletionRequestView]:
    deletion = await create_deletion_request(
        db, user, payload, grace_days=get_settings().account_deletion_grace_days
    )
    response.delete_cookie("hg_access")
    response.delete_cookie("hg_refresh")
    await db.commit()
    return ApiResponse(data=DeletionRequestView.model_validate(deletion))


@router.get("/deletion", response_model=ApiResponse[list[DeletionRequestView]])
async def deletion_status(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[list[DeletionRequestView]]:
    rows = (
        await db.scalars(
            select(AccountDeletionRequest)
            .where(AccountDeletionRequest.user_id == user.id)
            .order_by(AccountDeletionRequest.requested_at.desc())
            .limit(10)
        )
    ).all()
    return ApiResponse(data=[DeletionRequestView.model_validate(row) for row in rows])


@router.post("/deletion/{request_id}/confirm", response_model=ApiResponse[DeletionRequestView])
async def deletion_confirm(
    request_id: uuid.UUID,
    payload: DeletionConfirm,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DeletionRequestView]:
    deletion = await confirm_deletion(db, user, request_id, payload.confirmation_phrase)
    response.delete_cookie("hg_access")
    response.delete_cookie("hg_refresh")
    await db.commit()
    return ApiResponse(data=DeletionRequestView.model_validate(deletion))
