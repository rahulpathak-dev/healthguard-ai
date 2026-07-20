import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.logging import get_logger
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.profiles.models import ProfileKind, ProfilePermission
from app.profiles.schemas import (
    PermissionCreate,
    PermissionView,
    ProfileCreate,
    ProfileUpdate,
    ProfileView,
)
from app.profiles.service import (
    create_profile,
    get_accessible_profile,
    grant_permission,
    list_accessible_profiles,
    update_profile,
)

router = APIRouter()
logger = get_logger()


def view(profile: object, is_owner: bool, can_edit: bool) -> ProfileView:
    result = ProfileView.model_validate(profile)
    return result.model_copy(update={"is_owner": is_owner, "can_edit": can_edit})


@router.get("", response_model=ApiResponse[list[ProfileView]])
async def list_profiles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[ProfileView]]:
    profiles = await list_accessible_profiles(db, user.id)
    return ApiResponse(data=[view(profile, owner, edit) for profile, owner, edit in profiles])


@router.post("", response_model=ApiResponse[ProfileView], status_code=201)
async def add_profile(
    payload: ProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProfileView]:
    try:
        profile = await create_profile(db, user, payload)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A matching profile already exists") from exc
    logger.info(
        "health_profile_created",
        actor_id=str(user.id),
        profile_id=str(profile.id),
        kind=profile.kind.value,
    )
    return ApiResponse(data=view(profile, True, True))


@router.get("/{profile_id}", response_model=ApiResponse[ProfileView])
async def get_profile(
    profile_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProfileView]:
    profile, owner, edit = await get_accessible_profile(db, profile_id, user.id)
    return ApiResponse(data=view(profile, owner, edit))


@router.patch("/{profile_id}", response_model=ApiResponse[ProfileView])
async def edit_profile(
    profile_id: uuid.UUID,
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProfileView]:
    profile, owner, edit = await get_accessible_profile(db, profile_id, user.id, require_edit=True)
    if profile.kind == ProfileKind.PERSONAL and payload.relationship is not None:
        raise HTTPException(
            status_code=400, detail="A personal profile cannot have a family relationship"
        )
    if (
        profile.kind == ProfileKind.FAMILY
        and "relationship" in payload.model_fields_set
        and payload.relationship is None
    ):
        raise HTTPException(status_code=400, detail="A family relationship cannot be empty")
    try:
        await update_profile(db, profile, payload)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A matching profile already exists") from exc
    logger.info("health_profile_updated", actor_id=str(user.id), profile_id=str(profile.id))
    return ApiResponse(data=view(profile, owner, edit))


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    profile, owner, _ = await get_accessible_profile(db, profile_id, user.id, require_edit=True)
    if not owner:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.kind == ProfileKind.PERSONAL:
        raise HTTPException(status_code=409, detail="The personal profile cannot be deleted")
    await db.delete(profile)
    logger.warning("family_profile_deleted", actor_id=str(user.id), profile_id=str(profile.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{profile_id}/permissions", response_model=ApiResponse[list[PermissionView]])
async def list_permissions(
    profile_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[PermissionView]]:
    profile, owner, _ = await get_accessible_profile(db, profile_id, user.id)
    if not owner:
        raise HTTPException(status_code=404, detail="Profile not found")
    permissions = (
        await db.scalars(
            select(ProfilePermission).where(ProfilePermission.profile_id == profile.id)
        )
    ).all()
    return ApiResponse(data=[PermissionView.model_validate(item) for item in permissions])


@router.put("/{profile_id}/permissions", response_model=ApiResponse[PermissionView])
async def set_permission(
    profile_id: uuid.UUID,
    payload: PermissionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[PermissionView]:
    profile, owner, _ = await get_accessible_profile(db, profile_id, user.id)
    if not owner:
        raise HTTPException(status_code=404, detail="Profile not found")
    permission = await grant_permission(db, profile, payload.grantee_user_id, payload.level)
    logger.info(
        "profile_permission_changed",
        actor_id=str(user.id),
        profile_id=str(profile.id),
        grantee_id=str(permission.grantee_user_id),
        level=permission.level.value,
    )
    return ApiResponse(data=PermissionView.model_validate(permission))


@router.delete("/{profile_id}/permissions/{grantee_user_id}", status_code=204)
async def delete_permission(
    profile_id: uuid.UUID,
    grantee_user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    profile, owner, _ = await get_accessible_profile(db, profile_id, user.id)
    if not owner:
        raise HTTPException(status_code=404, detail="Profile not found")
    permission = await db.scalar(
        select(ProfilePermission).where(
            ProfilePermission.profile_id == profile.id,
            ProfilePermission.grantee_user_id == grantee_user_id,
        )
    )
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    await db.delete(permission)
    logger.info(
        "profile_permission_revoked",
        actor_id=str(user.id),
        profile_id=str(profile.id),
        grantee_id=str(grantee_user_id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
