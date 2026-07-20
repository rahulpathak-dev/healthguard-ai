from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.medicines.models import MedicineSearchHistory
from app.medicines.schemas import MedicineHistoryView, MedicineInformation
from app.medicines.service import search_medicine

router = APIRouter()


@router.get("/search", response_model=ApiResponse[MedicineInformation])
async def search(
    q: str = Query(min_length=2, max_length=120),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MedicineInformation]:
    result = await search_medicine(db, user=user, query=q)
    await db.commit()
    return ApiResponse(data=result)


@router.get("/history", response_model=ApiResponse[list[MedicineHistoryView]])
async def history(
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[MedicineHistoryView]]:
    rows = (
        await db.scalars(
            select(MedicineSearchHistory)
            .where(MedicineSearchHistory.user_id == user.id)
            .order_by(MedicineSearchHistory.created_at.desc())
            .limit(limit)
        )
    ).all()
    return ApiResponse(data=[MedicineHistoryView.model_validate(row) for row in rows])
