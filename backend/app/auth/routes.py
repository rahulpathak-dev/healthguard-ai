import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.auth.dependencies import AuthContext, get_auth_context, get_current_user, require_admin
from app.auth.models import Session, User
from app.auth.notifier import notifier
from app.auth.rate_limit import client_ip, enforce_rate_limit
from app.auth.schemas import (
    EmailRequest,
    LoginRequest,
    MessageView,
    RegisterRequest,
    ResetPasswordRequest,
    RoleUpdateRequest,
    SessionView,
    TokenRequest,
    UserView,
)
from app.auth.security import create_access_token, digest_token, hash_password
from app.auth.service import (
    GENERIC_LOGIN_ERROR,
    authenticate_user,
    consume_action_token,
    create_action_token,
    create_session,
    find_user_by_email,
    register_user,
    revoke_all_sessions,
    rotate_session,
)
from app.core.logging import get_logger
from app.core.responses import ApiResponse
from app.db.session import get_db_session

router = APIRouter()
logger = get_logger()
GENERIC_ACCOUNT_MESSAGE = "If the account is eligible, instructions will be sent shortly."


def request_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


@router.post("/register", response_model=ApiResponse[MessageView], status_code=202)
async def register(
    payload: RegisterRequest,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MessageView]:
    ip = client_ip(request)
    await enforce_rate_limit("register", ip, 5, 3600)
    user, token = await register_user(db, str(payload.email), payload.password)
    if user and token:
        background.add_task(notifier.send_verification, user.email, token)
        logger.info("user_registered", user_id=str(user.id), ip=ip)
    return ApiResponse(data=MessageView(message=GENERIC_ACCOUNT_MESSAGE))


@router.post("/verify-email", response_model=ApiResponse[MessageView])
async def verify_email(
    payload: TokenRequest, request: Request, db: AsyncSession = Depends(get_db_session)
) -> ApiResponse[MessageView]:
    await enforce_rate_limit("verify", client_ip(request), 10, 3600)
    user = await consume_action_token(db, payload.token, "verify_email")
    if user is None:
        raise HTTPException(status_code=400, detail="This verification link is invalid or expired")
    user.is_email_verified = True
    logger.info("email_verified", user_id=str(user.id))
    return ApiResponse(data=MessageView(message="Email address verified"))


@router.post("/login", response_model=ApiResponse[UserView])
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[UserView]:
    ip = client_ip(request)
    email_key = digest_token(str(payload.email).strip().lower())[:24]
    await enforce_rate_limit("login-ip", ip, 20, 900)
    await enforce_rate_limit("login-account", email_key, 8, 900)
    user = await authenticate_user(db, str(payload.email), payload.password)
    if user is None:
        logger.warning("login_failed", account_key=email_key, ip=ip)
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    session, refresh = await create_session(db, user, request_agent(request), ip)
    set_auth_cookies(response, create_access_token(user, session.id), refresh)
    logger.info("login_succeeded", user_id=str(user.id), session_id=str(session.id), ip=ip)
    return ApiResponse(data=UserView.model_validate(user))


@router.post("/refresh", response_model=ApiResponse[UserView])
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="hg_refresh"),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[UserView]:
    await enforce_rate_limit("refresh", client_ip(request), 30, 300)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    rotated = await rotate_session(db, refresh_token, request_agent(request), client_ip(request))
    if rotated is None:
        clear_auth_cookies(response)
        logger.warning("refresh_rejected", ip=client_ip(request), possible_replay=True)
        raise HTTPException(status_code=401, detail="Authentication required")
    user, session, new_refresh = rotated
    set_auth_cookies(response, create_access_token(user, session.id), new_refresh)
    logger.info("refresh_rotated", user_id=str(user.id), session_id=str(session.id))
    return ApiResponse(data=UserView.model_validate(user))


@router.post("/logout", response_model=ApiResponse[MessageView])
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="hg_refresh"),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MessageView]:
    if refresh_token:
        session = await db.scalar(
            select(Session).where(Session.refresh_token_hash == digest_token(refresh_token))
        )
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            logger.info(
                "session_logged_out", user_id=str(session.user_id), session_id=str(session.id)
            )
    clear_auth_cookies(response)
    return ApiResponse(data=MessageView(message="Signed out"))


@router.post("/forgot-password", response_model=ApiResponse[MessageView], status_code=202)
async def forgot_password(
    payload: EmailRequest,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MessageView]:
    ip = client_ip(request)
    await enforce_rate_limit("forgot", ip, 5, 3600)
    user = await find_user_by_email(db, str(payload.email))
    if user and user.is_active:
        token = await create_action_token(db, user.id, "password_reset", timedelta(minutes=30))
        background.add_task(notifier.send_password_reset, user.email, token)
        logger.info("password_reset_requested", user_id=str(user.id), ip=ip)
    return ApiResponse(data=MessageView(message=GENERIC_ACCOUNT_MESSAGE))


@router.post("/reset-password", response_model=ApiResponse[MessageView])
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MessageView]:
    await enforce_rate_limit("reset", client_ip(request), 10, 3600)
    user = await consume_action_token(db, payload.token, "password_reset")
    if user is None:
        raise HTTPException(status_code=400, detail="This reset link is invalid or expired")
    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = datetime.now(UTC)
    user.failed_login_attempts = 0
    user.locked_until = None
    await revoke_all_sessions(db, user.id)
    logger.info("password_reset_completed", user_id=str(user.id))
    return ApiResponse(data=MessageView(message="Password reset. Sign in with your new password."))


@router.get("/me", response_model=ApiResponse[UserView])
async def me(user: User = Depends(get_current_user)) -> ApiResponse[UserView]:
    return ApiResponse(data=UserView.model_validate(user))


@router.get("/sessions", response_model=ApiResponse[list[SessionView]])
async def sessions(
    context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[SessionView]]:
    rows = (
        await db.scalars(
            select(Session)
            .where(
                Session.user_id == context.user.id,
                Session.revoked_at.is_(None),
                Session.expires_at > datetime.now(UTC),
            )
            .order_by(Session.last_seen_at.desc())
        )
    ).all()
    return ApiResponse(
        data=[
            SessionView(
                id=row.id,
                user_agent=row.user_agent,
                ip_address=row.ip_address,
                created_at=row.created_at,
                last_seen_at=row.last_seen_at,
                expires_at=row.expires_at,
                is_current=row.id == context.session.id,
            )
            for row in rows
        ]
    )


@router.delete("/sessions/{session_id}", response_model=ApiResponse[MessageView])
async def revoke_session(
    session_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MessageView]:
    session = await db.get(Session, session_id)
    if session is None or session.user_id != context.user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    session.revoked_at = datetime.now(UTC)
    logger.info("session_revoked", user_id=str(context.user.id), session_id=str(session.id))
    return ApiResponse(data=MessageView(message="Session revoked"))


@router.post("/logout-all", response_model=ApiResponse[MessageView])
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MessageView]:
    await revoke_all_sessions(db, user.id)
    clear_auth_cookies(response)
    logger.info("all_sessions_revoked", user_id=str(user.id))
    return ApiResponse(data=MessageView(message="Signed out on all devices"))


@router.patch("/users/{user_id}/role", response_model=ApiResponse[UserView])
async def update_role(
    user_id: uuid.UUID,
    payload: RoleUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[UserView]:
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Administrators cannot change their own role")
    target.role = payload.role
    await revoke_all_sessions(db, target.id)
    logger.warning(
        "role_changed", actor_id=str(admin.id), target_id=str(target.id), role=target.role.value
    )
    return ApiResponse(data=UserView.model_validate(target))
