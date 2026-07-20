import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.auth.models import User, UserRole
from app.sharing.models import RecordShareGrant
from app.sharing.schemas import ShareGrantCreate
from app.sharing.service import share_is_active


def test_share_grant_schema_rejects_duplicate_record_ids() -> None:
    record_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Duplicate"):
        ShareGrantCreate(
            profile_id=uuid.uuid4(),
            doctor_user_id=uuid.uuid4(),
            record_ids=[record_id, record_id],
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )


def test_doctor_role_alone_is_not_a_share_grant() -> None:
    doctor = User(
        id=uuid.uuid4(),
        email="doctor@example.com",
        password_hash="unused",
        role=UserRole.DOCTOR,
        is_active=True,
        is_email_verified=True,
    )
    grant = RecordShareGrant(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        doctor_user_id=uuid.uuid4(),
        scope="read",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked_at=None,
        created_at=datetime.now(UTC),
    )
    assert doctor.id != grant.doctor_user_id
    assert share_is_active(grant)


def grant(*, expires_at: datetime, revoked_at: datetime | None = None) -> RecordShareGrant:
    return RecordShareGrant(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        doctor_user_id=uuid.uuid4(),
        scope="read",
        expires_at=expires_at,
        revoked_at=revoked_at,
        created_at=datetime.now(UTC),
    )


def test_revoked_and_expired_grants_are_inactive() -> None:
    active = grant(expires_at=datetime.now(UTC) + timedelta(minutes=5))
    revoked = grant(
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        revoked_at=datetime.now(UTC),
    )
    expired = grant(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    assert share_is_active(active)
    assert not share_is_active(revoked)
    assert not share_is_active(expired)
