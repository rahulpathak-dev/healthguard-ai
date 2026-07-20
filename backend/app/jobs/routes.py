import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.core.responses import ApiResponse
from app.db.redis import get_redis
from app.db.session import get_db_session
from app.jobs.schemas import JobHealth, JobView
from app.jobs.service import job_counts

router = APIRouter()


@router.get("/health", response_model=ApiResponse[JobHealth])
async def health(
    db: AsyncSession = Depends(get_db_session), admin: User = Depends(require_admin)
) -> ApiResponse[JobHealth]:
    _ = admin
    counts = await job_counts(db)
    redis_status = "ok"
    try:
        await get_redis().ping()
    except Exception:
        redis_status = "unavailable"
    return ApiResponse(
        data=JobHealth(
            **counts,
            redis=redis_status,
            status="attention" if counts["dead_lettered"] or redis_status != "ok" else "ok",
        )
    )


@router.get("/{job_id}", response_model=ApiResponse[JobView])
async def detail(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
) -> ApiResponse[JobView]:
    _ = admin
    from app.jobs.models import BackgroundJob

    job = await db.get(BackgroundJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return ApiResponse(data=JobView.model_validate(job))
