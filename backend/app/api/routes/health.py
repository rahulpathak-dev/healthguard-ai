from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.core.observability import metrics_snapshot
from app.core.responses import ApiResponse
from app.db.redis import get_redis
from app.db.session import engine

router = APIRouter()


@router.get("/health/live", response_model=ApiResponse[dict[str, str]])
async def liveness() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "ok"})


@router.get("/health/ready", response_model=ApiResponse[dict[str, str]])
async def readiness() -> ApiResponse[dict[str, str]]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        await get_redis().ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="A required service is unavailable") from exc
    return ApiResponse(data={"status": "ready", "database": "ok", "redis": "ok"})


@router.get("/health/metrics", response_model=ApiResponse[dict[str, float | int]])
async def metrics() -> ApiResponse[dict[str, float | int]]:
    return ApiResponse(data=metrics_snapshot())
