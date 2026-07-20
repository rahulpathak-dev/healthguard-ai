from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response

from app.core.config import get_settings

CSP = "; ".join(
    [
        "default-src 'self'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
        "form-action 'self'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "style-src 'self' 'unsafe-inline'",
        "script-src 'self'",
        "connect-src 'self'",
        "upgrade-insecure-requests",
    ]
)
CSRF_ORIGIN_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def allowed_origins() -> set[str]:
    return {str(origin).rstrip("/") for origin in get_settings().cors_origins}


def validate_origin_for_unsafe_method(request: Request) -> None:
    if request.method not in CSRF_ORIGIN_METHODS:
        return
    if not (request.cookies.get("hg_access") or request.cookies.get("hg_refresh")):
        return
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in allowed_origins():
        raise HTTPException(status_code=403, detail="Cross-site request origin is not allowed")


async def security_headers_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    validate_origin_for_unsafe_method(request)
    response = await call_next(request)
    settings = get_settings()
    response.headers.setdefault("Content-Security-Policy", CSP)
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=()",
    )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    if settings.environment == "production":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload",
        )
    return response
