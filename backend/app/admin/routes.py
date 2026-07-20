import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import AdminAuditLog
from app.admin.schemas import (
    AdminAuditLogView,
    AdminOverview,
    DoctorVerificationUpdate,
    DoctorVerificationView,
    FlaggedConversationReview,
    KnowledgeSourceReview,
    MisinformationReview,
    PlatformConfiguration,
    RedactedUserView,
    SafetyEventReview,
    SourceStatusUpdate,
    UserStatusUpdate,
)
from app.admin.service import (
    count_messages,
    email_domain,
    job_health,
    overview,
    platform_config,
    require_confirmation,
    update_doctor_verification,
    update_source_status,
    update_user_status,
)
from app.ai_safety.models import SafetyEvent
from app.auth.dependencies import require_admin
from app.auth.models import User
from app.core.responses import ApiResponse
from app.dashboard.models import Conversation
from app.db.session import get_db_session
from app.misinformation.models import MisinformationCheck
from app.rag.models import KnowledgeSource
from app.sharing.models import DoctorProfile

router = APIRouter()


@router.get("/overview", response_model=ApiResponse[AdminOverview])
async def admin_overview(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[AdminOverview]:
    _ = admin
    return ApiResponse(data=await overview(db))


@router.get("/users", response_model=ApiResponse[list[RedactedUserView]])
async def users(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[RedactedUserView]]:
    _ = admin
    rows = (await db.scalars(select(User).order_by(User.created_at.desc()).limit(100))).all()
    return ApiResponse(
        data=[
            RedactedUserView(
                id=row.id,
                email_domain=email_domain(row.email),
                role=row.role.value,
                is_active=row.is_active,
                is_email_verified=row.is_email_verified,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


@router.put("/users/{user_id}/status", response_model=ApiResponse[RedactedUserView])
async def set_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[RedactedUserView]:
    require_confirmation(payload)
    row = await update_user_status(
        db, admin=admin, user_id=user_id, active=payload.status == "active", reason=payload.reason
    )
    await db.commit()
    return ApiResponse(
        data=RedactedUserView(
            id=row.id,
            email_domain=email_domain(row.email),
            role=row.role.value,
            is_active=row.is_active,
            is_email_verified=row.is_email_verified,
            created_at=row.created_at,
        )
    )


@router.get("/doctors", response_model=ApiResponse[list[DoctorVerificationView]])
async def doctor_verification_queue(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[DoctorVerificationView]]:
    _ = admin
    rows = (
        await db.scalars(
            select(DoctorProfile).order_by(
                DoctorProfile.verification_status.asc(), DoctorProfile.created_at.desc()
            )
        )
    ).all()
    return ApiResponse(
        data=[DoctorVerificationView.model_validate(row, from_attributes=True) for row in rows]
    )


@router.put("/doctors/{doctor_id}/verification", response_model=ApiResponse[DoctorVerificationView])
async def verify_doctor(
    doctor_id: uuid.UUID,
    payload: DoctorVerificationUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[DoctorVerificationView]:
    require_confirmation(payload)
    profile = await update_doctor_verification(
        db,
        admin=admin,
        doctor_id=doctor_id,
        status=payload.verification_status,
        reason=payload.reason,
    )
    await db.commit()
    return ApiResponse(data=DoctorVerificationView.model_validate(profile, from_attributes=True))


@router.get("/safety-events", response_model=ApiResponse[list[SafetyEventReview]])
async def safety_events(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[SafetyEventReview]]:
    _ = admin
    rows = (
        await db.scalars(select(SafetyEvent).order_by(SafetyEvent.created_at.desc()).limit(100))
    ).all()
    return ApiResponse(
        data=[SafetyEventReview.model_validate(row, from_attributes=True) for row in rows]
    )


@router.get("/flagged-conversations", response_model=ApiResponse[list[FlaggedConversationReview]])
async def flagged_conversations(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[FlaggedConversationReview]]:
    _ = admin
    rows = (
        await db.scalars(
            select(Conversation)
            .join(SafetyEvent, SafetyEvent.conversation_id == Conversation.id)
            .order_by(SafetyEvent.created_at.desc())
            .limit(50)
        )
    ).all()
    views = []
    seen: set[uuid.UUID] = set()
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        views.append(
            FlaggedConversationReview(
                id=row.id,
                title=row.title,
                language=row.language,
                created_at=row.created_at,
                last_message_at=row.last_message_at,
                message_count=await count_messages(db, row.id),
            )
        )
    return ApiResponse(data=views)


@router.get("/misinformation", response_model=ApiResponse[list[MisinformationReview]])
async def misinformation_review(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[MisinformationReview]]:
    _ = admin
    rows = (
        await db.scalars(
            select(MisinformationCheck).order_by(MisinformationCheck.created_at.desc()).limit(100)
        )
    ).all()
    reviews: list[MisinformationReview] = []
    for row in rows:
        trusted_sources = row.evidence_json.get("trusted_sources", [])
        reviews.append(
            MisinformationReview(
                id=row.id,
                verdict=row.verdict,
                claim_summary=row.claim_summary,
                trusted_source_count=len(trusted_sources)
                if isinstance(trusted_sources, list)
                else 0,
                created_at=row.created_at,
            )
        )
    return ApiResponse(data=reviews)


@router.get("/knowledge-sources", response_model=ApiResponse[list[KnowledgeSourceReview]])
async def knowledge_sources(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[KnowledgeSourceReview]]:
    _ = admin
    rows = (
        await db.scalars(select(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()))
    ).all()
    return ApiResponse(
        data=[KnowledgeSourceReview.model_validate(row, from_attributes=True) for row in rows]
    )


@router.put(
    "/knowledge-sources/{source_id}/status", response_model=ApiResponse[KnowledgeSourceReview]
)
async def source_status(
    source_id: uuid.UUID,
    payload: SourceStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[KnowledgeSourceReview]:
    require_confirmation(payload)
    source = await update_source_status(
        db, admin=admin, source_id=source_id, status=payload.approval_status, reason=payload.reason
    )
    await db.commit()
    return ApiResponse(data=KnowledgeSourceReview.model_validate(source, from_attributes=True))


@router.get("/audit-logs", response_model=ApiResponse[list[AdminAuditLogView]])
async def audit_logs(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[list[AdminAuditLogView]]:
    _ = admin
    rows = (
        await db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(200))
    ).all()
    return ApiResponse(data=[AdminAuditLogView.model_validate(row) for row in rows])


@router.get("/system-health", response_model=ApiResponse[dict[str, int | str]])
async def system_health(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[dict[str, int | str]]:
    _ = admin
    return ApiResponse(data=await job_health(db))


@router.get("/configuration", response_model=ApiResponse[PlatformConfiguration])
async def configuration(admin: User = Depends(require_admin)) -> ApiResponse[PlatformConfiguration]:
    _ = admin
    return ApiResponse(data=await platform_config())
