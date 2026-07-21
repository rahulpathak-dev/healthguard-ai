import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from pwdlib import PasswordHash

from app.auth.models import User, UserRole
from app.core.config import get_settings

password_hash = PasswordHash.recommended()
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def random_token() -> str:
    return secrets.token_urlsafe(48)


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user: User, session_id: uuid.UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "sid": str(session_id),
        "role": user.role.value,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "iss": "healthguard-api",
        "aud": "healthguard-web",
    }
    return jwt.encode(payload, settings.token_secret.get_secret_value(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.token_secret.get_secret_value(),
        algorithms=[JWT_ALGORITHM],
        audience="healthguard-web",
        issuer="healthguard-api",
        options={"require": ["sub", "sid", "role", "type", "jti", "exp"]},
    )
    if payload.get("type") != "access" or payload.get("role") not in {r.value for r in UserRole}:
        raise jwt.InvalidTokenError("Invalid token claims")
    return cast(dict[str, Any], payload)
