import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import ActionToken, Session, User, UserRole
from app.auth.security import digest_token, hash_password, random_token, verify_password
from app.core.config import get_settings

GENERIC_LOGIN_ERROR = "Invalid email or password"
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


async def find_user_by_email(db: AsyncSession, email: str) -> User | None:
    return cast(
        User | None, await db.scalar(select(User).where(User.email == email.strip().lower()))
    )


async def register_user(
    db: AsyncSession, email: str, password: str
) -> tuple[User | None, str | None]:
    normalized = email.strip().lower()
    if await find_user_by_email(db, normalized):
        hash_password(password)
        return None, None
    user = User(email=normalized, password_hash=hash_password(password), role=UserRole.USER)
    db.add(user)
    await db.flush()
    token = await create_action_token(db, user.id, "verify_email", timedelta(hours=24))
    return user, token


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await find_user_by_email(db, email)
    now = datetime.now(UTC)
    if user is None or user.password_hash is None:
        hash_password(password)
        return None
    if user.locked_until and user.locked_until > now:
        return None
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_login_attempts = 0
        await db.flush()
        return None
    if not user.is_active:
        return None
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.flush()
    return user


async def create_session(
    db: AsyncSession,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
    family_id: uuid.UUID | None = None,
) -> tuple[Session, str]:
    settings = get_settings()
    now = datetime.now(UTC)
    refresh_token = random_token()
    session = Session(
        user_id=user.id,
        family_id=family_id or uuid.uuid4(),
        refresh_token_hash=digest_token(refresh_token),
        user_agent=(user_agent or "")[:512] or None,
        ip_address=ip_address,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    await db.flush()
    return session, refresh_token


async def rotate_session(
    db: AsyncSession,
    raw_token: str,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[User, Session, str] | None:
    now = datetime.now(UTC)
    old = await db.scalar(
        select(Session)
        .where(Session.refresh_token_hash == digest_token(raw_token))
        .with_for_update()
    )
    if old is None:
        return None
    if old.revoked_at is not None or old.replaced_by_id is not None:
        await db.execute(
            update(Session).where(Session.family_id == old.family_id).values(revoked_at=now)
        )
        return None
    if old.expires_at <= now:
        old.revoked_at = now
        return None
    user = await db.get(User, old.user_id)
    if user is None or not user.is_active:
        old.revoked_at = now
        return None
    new_session, new_token = await create_session(
        db, user, user_agent, ip_address, family_id=old.family_id
    )
    old.revoked_at = now
    old.replaced_by_id = new_session.id
    await db.flush()
    return user, new_session, new_token


async def create_action_token(
    db: AsyncSession, user_id: uuid.UUID, purpose: str, lifetime: timedelta
) -> str:
    now = datetime.now(UTC)
    await db.execute(
        update(ActionToken)
        .where(
            ActionToken.user_id == user_id,
            ActionToken.purpose == purpose,
            ActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    raw = random_token()
    db.add(
        ActionToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=digest_token(raw),
            expires_at=now + lifetime,
        )
    )
    await db.flush()
    return raw


async def consume_action_token(db: AsyncSession, raw: str, purpose: str) -> User | None:
    now = datetime.now(UTC)
    token = await db.scalar(
        select(ActionToken)
        .where(ActionToken.token_hash == digest_token(raw), ActionToken.purpose == purpose)
        .with_for_update()
    )
    if token is None or token.used_at is not None or token.expires_at <= now:
        return None
    token.used_at = now
    return await db.get(User, token.user_id)


async def revoke_all_sessions(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(Session)
        .where(Session.user_id == user_id, Session.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
