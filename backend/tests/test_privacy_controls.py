import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.auth.models import User, UserRole
from app.auth.security import digest_token
from app.privacy.models import DataExportRequest
from app.privacy.schemas import DeletionCreate, PrivacyPreferencesUpdate
from app.privacy.service import DELETE_PHRASE, update_preferences, validate_export_token


def test_deletion_request_requires_exact_confirmation_phrase() -> None:
    with pytest.raises(ValueError):
        DeletionCreate(confirmation_phrase="short")
    payload = DeletionCreate(confirmation_phrase=DELETE_PHRASE)
    assert payload.confirmation_phrase == DELETE_PHRASE


@pytest.mark.asyncio
async def test_export_token_rejects_expired_or_tampered_links() -> None:
    export = DataExportRequest(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        job_id=None,
        status="ready",
        export_path="export.json",
        download_token_hash=digest_token("valid-token"),
        download_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        requested_at=datetime.now(UTC),
    )

    class FakeDb:
        async def get(self, model, key):  # noqa: ANN001
            return export

    with pytest.raises(Exception, match="expired|invalid"):
        await validate_export_token(FakeDb(), export.id, "valid-token")  # type: ignore[arg-type]
    export.download_expires_at = datetime.now(UTC) + timedelta(minutes=5)
    with pytest.raises(Exception, match="expired|invalid"):
        await validate_export_token(FakeDb(), export.id, "wrong-token")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_privacy_preferences_keep_essential_cookies_enabled() -> None:
    user = User(
        id=uuid.uuid4(),
        email="a@example.com",
        password_hash="x",
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True,
    )

    class FakeResult:
        def __init__(self) -> None:
            self.pref = None

        async def scalar(self, statement):  # noqa: ANN001
            return self.pref

        def add(self, pref):  # noqa: ANN001
            self.pref = pref

        async def flush(self) -> None:
            return None

    db = FakeResult()
    pref = await update_preferences(
        db,  # type: ignore[arg-type]
        user,
        PrivacyPreferencesUpdate(
            cookie_preferences={"essential": False, "analytics": True},
            notification_preferences={"email": False},
        ),
    )
    assert pref.cookie_preferences_json["essential"] is True
    assert pref.cookie_preferences_json["analytics"] is True
