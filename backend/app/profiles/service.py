import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.profiles.models import (
    Allergy,
    ChronicCondition,
    CurrentMedicine,
    EmergencyContact,
    HealthProfile,
    PermissionLevel,
    ProfileKind,
    ProfilePermission,
)
from app.profiles.schemas import ProfileCreate, ProfileUpdate

PROFILE_LOAD_OPTIONS = (
    selectinload(HealthProfile.emergency_contacts),
    selectinload(HealthProfile.allergies),
    selectinload(HealthProfile.medicines),
    selectinload(HealthProfile.chronic_conditions),
)


def profile_dedupe_key(
    name: str, relationship: str | None, birth_date: object, kind: ProfileKind
) -> str:
    identity = "|".join(
        [
            " ".join(name.lower().split()),
            " ".join((relationship or "").lower().split()),
            str(birth_date or ""),
            kind.value,
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


async def list_accessible_profiles(
    db: AsyncSession, user_id: uuid.UUID
) -> list[tuple[HealthProfile, bool, bool]]:
    permission = ProfilePermission
    statement = (
        select(HealthProfile, permission.level)
        .outerjoin(
            permission,
            (permission.profile_id == HealthProfile.id) & (permission.grantee_user_id == user_id),
        )
        .where(or_(HealthProfile.owner_user_id == user_id, permission.grantee_user_id == user_id))
        .options(*PROFILE_LOAD_OPTIONS)
        .order_by(HealthProfile.kind, HealthProfile.display_name)
    )
    rows = (await db.execute(statement)).unique().all()
    return [
        (
            profile,
            profile.owner_user_id == user_id,
            profile.owner_user_id == user_id or level == PermissionLevel.EDIT,
        )
        for profile, level in rows
    ]


async def get_accessible_profile(
    db: AsyncSession,
    profile_id: uuid.UUID,
    user_id: uuid.UUID,
    require_edit: bool = False,
) -> tuple[HealthProfile, bool, bool]:
    profile = await db.scalar(
        select(HealthProfile).where(HealthProfile.id == profile_id).options(*PROFILE_LOAD_OPTIONS)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    is_owner = profile.owner_user_id == user_id
    permission = None
    if not is_owner:
        permission = await db.scalar(
            select(ProfilePermission).where(
                ProfilePermission.profile_id == profile_id,
                ProfilePermission.grantee_user_id == user_id,
            )
        )
    can_edit = is_owner or (permission is not None and permission.level == PermissionLevel.EDIT)
    if (not is_owner and permission is None) or (require_edit and not can_edit):
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile, is_owner, can_edit


def apply_nested_records(profile: HealthProfile, payload: ProfileCreate | ProfileUpdate) -> None:
    if payload.emergency_contacts is not None:
        profile.emergency_contacts = [
            EmergencyContact(**item.model_dump()) for item in payload.emergency_contacts
        ]
    if payload.allergies is not None:
        profile.allergies = [Allergy(**item.model_dump()) for item in payload.allergies]
    if payload.medicines is not None:
        profile.medicines = [CurrentMedicine(**item.model_dump()) for item in payload.medicines]
    if payload.chronic_conditions is not None:
        profile.chronic_conditions = [
            ChronicCondition(**item.model_dump()) for item in payload.chronic_conditions
        ]


async def create_profile(db: AsyncSession, owner: User, payload: ProfileCreate) -> HealthProfile:
    count = await db.scalar(
        select(func.count())
        .select_from(HealthProfile)
        .where(HealthProfile.owner_user_id == owner.id)
    )
    if count is not None and count >= 25:
        raise HTTPException(status_code=409, detail="The profile limit has been reached")
    now = datetime.now(UTC)
    profile = HealthProfile(
        owner_user_id=owner.id,
        kind=payload.kind,
        display_name=payload.display_name,
        normalized_name=" ".join(payload.display_name.lower().split()),
        relationship=payload.relationship,
        dedupe_key=profile_dedupe_key(
            payload.display_name, payload.relationship, payload.date_of_birth, payload.kind
        ),
        date_of_birth=payload.date_of_birth,
        blood_group=payload.blood_group,
        sex_at_birth=payload.sex_at_birth,
        gender_identity=payload.gender_identity,
        pronouns=payload.pronouns,
        avatar_url=str(payload.avatar_url) if payload.avatar_url else None,
        locale=payload.locale,
        timezone=payload.timezone,
        notes=payload.notes,
        allow_doctor_access=payload.allow_doctor_access or False,
        share_with_family=payload.share_with_family or False,
        created_at=now,
        updated_at=now,
    )
    apply_nested_records(profile, payload)
    db.add(profile)
    await db.flush()
    return profile


async def update_profile(
    db: AsyncSession, profile: HealthProfile, payload: ProfileUpdate
) -> HealthProfile:
    scalar_fields = {
        "display_name",
        "relationship",
        "date_of_birth",
        "blood_group",
        "sex_at_birth",
        "gender_identity",
        "pronouns",
        "locale",
        "timezone",
        "notes",
        "allow_doctor_access",
        "share_with_family",
    }
    changes = payload.model_dump(exclude_unset=True)
    for field in scalar_fields:
        if field in changes:
            setattr(profile, field, changes[field])
    if "avatar_url" in changes:
        profile.avatar_url = str(payload.avatar_url) if payload.avatar_url else None
    apply_nested_records(profile, payload)
    profile.normalized_name = " ".join(profile.display_name.lower().split())
    profile.dedupe_key = profile_dedupe_key(
        profile.display_name, profile.relationship, profile.date_of_birth, profile.kind
    )
    profile.updated_at = datetime.now(UTC)
    await db.flush()
    return profile


async def grant_permission(
    db: AsyncSession,
    profile: HealthProfile,
    grantee_user_id: uuid.UUID,
    level: PermissionLevel,
) -> ProfilePermission:
    if grantee_user_id == profile.owner_user_id:
        raise HTTPException(status_code=400, detail="The profile owner already has access")
    grantee = await db.get(User, grantee_user_id)
    if grantee is None or not grantee.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    permission = await db.scalar(
        select(ProfilePermission).where(
            ProfilePermission.profile_id == profile.id,
            ProfilePermission.grantee_user_id == grantee_user_id,
        )
    )
    if permission:
        permission.level = level
    else:
        permission = ProfilePermission(
            profile_id=profile.id,
            grantee_user_id=grantee_user_id,
            level=level,
            created_at=datetime.now(UTC),
        )
        db.add(permission)
    await db.flush()
    return permission
