from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_safety.models import SafetyReport
from app.ai_safety.schemas import SafetyReportCreate, SafetyReportView
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.chat.models import ChatMessage
from app.core.config import get_settings
from app.core.responses import ApiResponse
from app.dashboard.models import Conversation
from app.db.session import get_db_session

router = APIRouter()


@router.get("/disclaimer", response_model=ApiResponse[dict[str, str]])
async def disclaimer() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"disclaimer": get_settings().medical_disclaimer})


@router.post("/reports", response_model=ApiResponse[SafetyReportView], status_code=201)
async def create_report(
    payload: SafetyReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SafetyReportView]:
    if payload.message_id:
        message = await db.scalar(
            select(ChatMessage)
            .join(Conversation, Conversation.id == ChatMessage.conversation_id)
            .where(ChatMessage.id == payload.message_id, Conversation.owner_user_id == user.id)
        )
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
    report = SafetyReport(
        user_id=user.id,
        message_id=payload.message_id,
        category=payload.category,
        reason=payload.reason,
        status="open",
        created_at=datetime.now(UTC),
    )
    db.add(report)
    await db.flush()
    return ApiResponse(data=SafetyReportView.model_validate(report))
