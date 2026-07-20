import uuid

import pytest
from fastapi import HTTPException, Response
from pydantic import ValidationError

from app.auth.cookies import set_auth_cookies
from app.auth.dependencies import require_roles
from app.auth.models import User, UserRole
from app.auth.schemas import RegisterRequest
from app.auth.security import (
    create_access_token,
    decode_access_token,
    digest_token,
    hash_password,
    random_token,
    verify_password,
)
from app.auth.service import GENERIC_LOGIN_ERROR


def user(role: UserRole = UserRole.USER) -> User:
    return User(
        id=uuid.uuid4(),
        email="person@example.com",
        password_hash="unused",
        role=role,
        is_active=True,
        is_email_verified=True,
    )


def test_password_is_argon2_hashed_and_verifiable() -> None:
    plain = "LongAndSafePassword123"
    encoded = hash_password(plain)
    assert encoded != plain
    assert encoded.startswith("$argon2")
    assert verify_password(plain, encoded)


def test_refresh_secret_is_only_compared_by_digest() -> None:
    token = random_token()
    digest = digest_token(token)
    assert token not in digest
    assert len(digest) == 64


def test_access_token_has_fixed_security_claims() -> None:
    account = user(UserRole.DOCTOR)
    session_id = uuid.uuid4()
    claims = decode_access_token(create_access_token(account, session_id))
    assert claims["sub"] == str(account.id)
    assert claims["sid"] == str(session_id)
    assert claims["role"] == "doctor"
    assert claims["type"] == "access"


def test_registration_rejects_role_assignment() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest.model_validate(
            {
                "email": "person@example.com",
                "password": "LongPassword123",
                "role": "admin",
            }
        )


@pytest.mark.asyncio
async def test_regular_user_cannot_pass_admin_dependency() -> None:
    dependency = require_roles(UserRole.ADMIN)
    with pytest.raises(HTTPException) as exc:
        await dependency(user())
    assert exc.value.status_code == 403


def test_auth_cookies_are_http_only_and_same_site() -> None:
    response = Response()
    set_auth_cookies(response, "access-secret", "refresh-secret")
    cookies = response.headers.getlist("set-cookie")
    assert all("HttpOnly" in cookie for cookie in cookies)
    assert all("SameSite=lax" in cookie for cookie in cookies)
    assert not any(
        "access-secret" in cookie and "Path=/api/v1/auth" in cookie for cookie in cookies
    )


def test_login_error_does_not_reveal_account_state() -> None:
    assert GENERIC_LOGIN_ERROR == "Invalid email or password"
