import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Session, User, UserRole
from app.auth.security import decode_access_token
from app.db.session import get_db_session


class AuthContext:
    def __init__(self, user: User, session: Session) -> None:
        self.user = user
        self.session = session


async def get_auth_context(
    access_token: str | None = Cookie(default=None, alias="hg_access"),
    db: AsyncSession = Depends(get_db_session),
) -> AuthContext:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
    )
    if not access_token:
        raise unauthorized
    try:
        payload = decode_access_token(access_token)
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise unauthorized from exc
    session = await db.get(Session, session_id)
    user = await db.get(User, user_id)
    if (
        session is None
        or user is None
        or session.user_id != user.id
        or session.revoked_at is not None
        or session.expires_at <= datetime.now(UTC)
        or not user.is_active
        or payload.get("role") != user.role.value
    ):
        raise unauthorized
    return AuthContext(user, session)


async def get_current_user(context: AuthContext = Depends(get_auth_context)) -> User:
    return context.user


def require_roles(*roles: UserRole) -> Callable[..., Awaitable[User]]:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency


require_admin = require_roles(UserRole.ADMIN)
require_doctor_or_admin = require_roles(UserRole.DOCTOR, UserRole.ADMIN)
