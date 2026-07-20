import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.misinformation.models import MisinformationCheck, MisinformationFeedback
from app.misinformation.schemas import CheckCreate, CheckView, FeedbackCreate
from app.misinformation.service import check_claim

router = APIRouter()


@router.post("/checks", response_model=ApiResponse[CheckView], status_code=201)
async def create_check(
    payload: CheckCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CheckView]:
    check = await check_claim(db, user=user, payload=payload)
    await db.commit()
    return ApiResponse(data=CheckView.model_validate(check))


@router.get("/checks", response_model=ApiResponse[list[CheckView]])
async def history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[CheckView]]:
    rows = (
        await db.scalars(
            select(MisinformationCheck)
            .where(MisinformationCheck.user_id == user.id)
            .order_by(MisinformationCheck.created_at.desc())
            .limit(50)
        )
    ).all()
    return ApiResponse(data=[CheckView.model_validate(row) for row in rows])


@router.put("/checks/{check_id}/feedback", status_code=204)
async def feedback(
    check_id: uuid.UUID,
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    check = await db.scalar(
        select(MisinformationCheck).where(
            MisinformationCheck.id == check_id,
            MisinformationCheck.user_id == user.id,
        )
    )
    if check is None:
        raise HTTPException(status_code=404, detail="Check not found")
    db.add(
        MisinformationFeedback(
            check_id=check.id,
            user_id=user.id,
            rating=payload.rating,
            reason=payload.reason,
            created_at=datetime.now(UTC),
        )
    )
    await db.commit()
