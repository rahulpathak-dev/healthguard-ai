import pytest
from pydantic import ValidationError
from starlette.datastructures import Headers

from app.core.config import Settings
from app.core.security_headers import CSP, validate_origin_for_unsafe_method


def base_settings(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://test:test@localhost:5432/test",
        "redis_url": "redis://localhost:6379/15",
        "token_secret": "test-secret-that-is-longer-than-thirty-two-characters",
        "cookie_secure": False,
        "docs_enabled": True,
    }
    values.update(overrides)
    return values


def test_csp_blocks_frames_objects_and_untrusted_script_sources() -> None:
    assert "frame-ancestors 'none'" in CSP
    assert "object-src 'none'" in CSP
    assert "script-src 'self'" in CSP
    assert "default-src 'self'" in CSP


def test_production_requires_secure_cookie_https_app_url_and_closed_docs() -> None:
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(**base_settings(environment="production"))
    with pytest.raises(ValidationError, match="localhost"):
        Settings(
            **base_settings(
                environment="production",
                cookie_secure=True,
                docs_enabled=False,
                web_app_url="https://healthguard.example",
                cors_origins=["http://localhost:3000"],
            )
        )
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            **base_settings(
                environment="production",
                cookie_secure=True,
                docs_enabled=False,
                web_app_url="http://healthguard.example",
                cors_origins=["https://healthguard.example"],
            )
        )
    with pytest.raises(ValidationError, match="DOCS_ENABLED"):
        Settings(
            **base_settings(
                environment="production",
                cookie_secure=True,
                docs_enabled=True,
                web_app_url="https://healthguard.example",
                cors_origins=["https://healthguard.example"],
            )
        )


def test_smtp_password_requires_username() -> None:
    with pytest.raises(ValidationError, match="SMTP_USERNAME"):
        Settings(**base_settings(smtp_password="secret-password"))


class FakeRequest:
    method = "POST"
    cookies = {"hg_access": "cookie-present"}
    headers = Headers({"origin": "https://evil.example"})


def test_cookie_authenticated_unsafe_requests_validate_origin() -> None:
    with pytest.raises(Exception, match="origin"):
        validate_origin_for_unsafe_method(FakeRequest())  # type: ignore[arg-type]
