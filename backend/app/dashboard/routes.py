import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.dashboard.schemas import DashboardView
from app.dashboard.service import build_dashboard
from app.db.session import get_db_session

router = APIRouter()


@router.get("", response_model=ApiResponse[DashboardView])
async def dashboard(
    profile_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DashboardView]:
    return ApiResponse(data=await build_dashboard(db, user.id, profile_id))
