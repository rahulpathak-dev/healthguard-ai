import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth.models import User, UserRole
from app.profiles.models import HealthProfile, PermissionLevel, ProfileKind, ProfilePermission
from app.profiles.routes import delete_profile
from app.profiles.schemas import ProfileCreate
from app.profiles.service import get_accessible_profile, profile_dedupe_key


def profile(owner_id: uuid.UUID, kind: ProfileKind = ProfileKind.FAMILY) -> HealthProfile:
    now = datetime.now(UTC)
    return HealthProfile(
        id=uuid.uuid4(),
        owner_user_id=owner_id,
        kind=kind,
        display_name="Sam",
        normalized_name="sam",
        relationship="child" if kind == ProfileKind.FAMILY else None,
        dedupe_key="a" * 64,
        allow_doctor_access=True,
        share_with_family=True,
        created_at=now,
        updated_at=now,
        emergency_contacts=[],
        allergies=[],
        medicines=[],
        chronic_conditions=[],
    )


def user(user_id: uuid.UUID | None = None) -> User:
    return User(
        id=user_id or uuid.uuid4(),
        email="member@example.com",
        password_hash="unused",
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True,
    )


class ScalarQueue:
    def __init__(self, *values: Any) -> None:
        self.values = list(values)
        self.deleted: list[object] = []

    async def scalar(self, statement: object) -> Any:
        return self.values.pop(0)

    async def delete(self, value: object) -> None:
        self.deleted.append(value)


@pytest.mark.asyncio
async def test_privacy_flags_do_not_grant_cross_profile_access() -> None:
    owner_id = uuid.uuid4()
    stranger_id = uuid.uuid4()
    record = profile(owner_id)
    db = ScalarQueue(record, None)
    with pytest.raises(HTTPException) as exc:
        await get_accessible_profile(db, record.id, stranger_id)  # type: ignore[arg-type]
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_explicit_view_permission_never_allows_edit() -> None:
    owner_id = uuid.uuid4()
    grantee_id = uuid.uuid4()
    record = profile(owner_id)
    permission = ProfilePermission(
        profile_id=record.id,
        grantee_user_id=grantee_id,
        level=PermissionLevel.VIEW,
        created_at=datetime.now(UTC),
    )
    with pytest.raises(HTTPException) as exc:
        await get_accessible_profile(
            ScalarQueue(record, permission),
            record.id,
            grantee_id,
            require_edit=True,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_owner_can_access_profile() -> None:
    owner_id = uuid.uuid4()
    record = profile(owner_id)
    result, is_owner, can_edit = await get_accessible_profile(
        ScalarQueue(record),
        record.id,
        owner_id,  # type: ignore[arg-type]
    )
    assert result.id == record.id
    assert is_owner and can_edit


@pytest.mark.asyncio
async def test_personal_profile_cannot_be_deleted() -> None:
    owner = user()
    record = profile(owner.id, ProfileKind.PERSONAL)
    db = ScalarQueue(record)
    with pytest.raises(HTTPException) as exc:
        await delete_profile(record.id, owner, db)  # type: ignore[arg-type]
    assert exc.value.status_code == 409
    assert not db.deleted


def test_duplicate_key_normalizes_case_and_spacing() -> None:
    birth = date(2012, 4, 3)
    first = profile_dedupe_key("Sam Lee", "Child", birth, ProfileKind.FAMILY)
    second = profile_dedupe_key("  sam   lee ", " child ", birth, ProfileKind.FAMILY)
    assert first == second


@pytest.mark.parametrize("birth", [date.today() + timedelta(days=1), date(1800, 1, 1)])
def test_invalid_birth_dates_are_rejected(birth: date) -> None:
    with pytest.raises(ValidationError):
        ProfileCreate(kind="family", display_name="Sam", relationship="child", date_of_birth=birth)


def test_sensitive_fields_are_optional() -> None:
    value = ProfileCreate(kind="family", display_name="Sam", relationship="child")
    assert value.date_of_birth is None
    assert value.blood_group is None
    assert value.gender_identity is None
    assert value.allergies is None
