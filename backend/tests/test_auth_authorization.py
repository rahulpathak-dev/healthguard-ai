import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import HTTPException

from app.auth.dependencies import get_auth_context
from app.auth.models import Session, User, UserRole
from app.auth.security import create_access_token
from app.core.config import Settings


def make_user(role: UserRole = UserRole.USER) -> User:
    return User(
        id=uuid.uuid4(),
        email="member@example.com",
        password_hash="unused",
        role=role,
        is_active=True,
        is_email_verified=True,
    )


def make_session(user: User, revoked: bool = False) -> Session:
    now = datetime.now(UTC)
    return Session(
        id=uuid.uuid4(),
        user_id=user.id,
        family_id=uuid.uuid4(),
        refresh_token_hash="a" * 64,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=1),
        revoked_at=now if revoked else None,
    )


class FakeSession:
    def __init__(self, user: User, session: Session) -> None:
        self.user = user
        self.session = session

    async def get(self, model: type[Any], identifier: uuid.UUID) -> Any:
        if model is User and identifier == self.user.id:
            return self.user
        if model is Session and identifier == self.session.id:
            return self.session
        return None


@pytest.mark.asyncio
async def test_revoked_session_rejects_still_valid_access_token() -> None:
    user = make_user()
    session = make_session(user, revoked=True)
    token = create_access_token(user, session.id)
    with pytest.raises(HTTPException) as exc:
        await get_auth_context(token, FakeSession(user, session))  # type: ignore[arg-type]
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_stale_role_claim_cannot_gain_or_keep_privilege() -> None:
    user = make_user(UserRole.USER)
    session = make_session(user)
    token = create_access_token(user, session.id)
    user.role = UserRole.ADMIN
    with pytest.raises(HTTPException) as exc:
        await get_auth_context(token, FakeSession(user, session))  # type: ignore[arg-type]
    assert exc.value.status_code == 401


def test_production_rejects_insecure_auth_cookie() -> None:
    with pytest.raises(ValueError):
        Settings(
            environment="production",
            database_url="postgresql+asyncpg://user:pass@db/app",
            redis_url="redis://redis:6379/0",
            token_secret="x" * 40,
            cookie_secure=False,
        )
