from fastapi import Response

from app.core.config import get_settings


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "hg_access",
        access_token,
        max_age=settings.access_token_minutes * 60,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        "hg_refresh",
        refresh_token,
        max_age=settings.refresh_token_days * 86400,
        path=f"{settings.api_prefix}/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie("hg_access", path="/", domain=settings.cookie_domain)
    response.delete_cookie(
        "hg_refresh", path=f"{settings.api_prefix}/auth", domain=settings.cookie_domain
    )
