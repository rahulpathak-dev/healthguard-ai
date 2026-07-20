import uuid
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.dashboard.models import ReportAnalysis
from app.db.session import SessionFactory, get_db_session
from app.jobs.service import enqueue_job
from app.reports.schemas import ReportAnalysisCreate, ReportAnalysisView
from app.reports.service import create_analysis, owned_analysis, process_analysis

router = APIRouter()


async def run_analysis(analysis_id: uuid.UUID) -> None:
    async with SessionFactory() as db:
        await process_analysis(db, analysis_id)
        await db.commit()


@router.post("/analyses", response_model=ApiResponse[ReportAnalysisView], status_code=201)
async def create(
    payload: ReportAnalysisCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReportAnalysisView]:
    analysis = await create_analysis(db, user=user, payload=payload)
    if analysis.status == "pending":
        await enqueue_job(
            db,
            job_type="report_processing",
            payload={"analysis_id": str(analysis.id)},
            queue="reports",
            owner_user_id=user.id,
            idempotency_key=f"report-processing:{analysis.id}",
        )
    await db.commit()
    if analysis.status == "pending":
        background_tasks.add_task(run_analysis, analysis.id)
    return ApiResponse(data=ReportAnalysisView.model_validate(analysis))


@router.post("/analyses/{analysis_id}/retry", response_model=ApiResponse[ReportAnalysisView])
async def retry(
    analysis_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReportAnalysisView]:
    analysis = await owned_analysis(db, analysis_id, user.id)
    analysis.status = "pending"
    analysis.ocr_status = "queued"
    analysis.error_message = None
    await enqueue_job(
        db,
        job_type="report_processing_retry",
        payload={"analysis_id": str(analysis.id)},
        queue="reports",
        owner_user_id=user.id,
        idempotency_key=f"report-processing-retry:{analysis.id}:{datetime.now(UTC).timestamp()}",
    )
    await db.commit()
    background_tasks.add_task(run_analysis, analysis.id)
    return ApiResponse(data=ReportAnalysisView.model_validate(analysis))


@router.get("/analyses", response_model=ApiResponse[list[ReportAnalysisView]])
async def history(
    limit: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[ReportAnalysisView]]:
    rows = (
        await db.scalars(
            select(ReportAnalysis)
            .where(ReportAnalysis.owner_user_id == user.id)
            .order_by(ReportAnalysis.created_at.desc())
            .limit(min(limit, 50))
        )
    ).all()
    return ApiResponse(data=[ReportAnalysisView.model_validate(row) for row in rows])


@router.get("/analyses/{analysis_id}", response_model=ApiResponse[ReportAnalysisView])
async def detail(
    analysis_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReportAnalysisView]:
    analysis = await owned_analysis(db, analysis_id, user.id)
    return ApiResponse(data=ReportAnalysisView.model_validate(analysis))


@router.get("/analyses/{analysis_id}/download")
async def download(
    analysis_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PlainTextResponse:
    analysis = await owned_analysis(db, analysis_id, user.id)
    lines = [analysis.title, f"Generated: {datetime.now(UTC).isoformat()}", ""]
    explanation = analysis.explanation_json or {}
    lines.append(str(explanation.get("summary", "Explanation is not available.")))
    lines.append("")
    values = explanation.get("values", [])
    if not isinstance(values, list):
        values = []
    for value in values:
        if not isinstance(value, dict):
            continue
        typed_value = cast(dict[str, object], value)
        lines.append(
            f"- {typed_value.get('label')}: {typed_value.get('value')} "
            f"{typed_value.get('unit') or ''} "
            f"(report range: {typed_value.get('reference_range') or 'not readable'}, "
            f"flag: {typed_value.get('flag')})"
        )
    lines.append("")
    lines.append(str(explanation.get("disclaimer", "")))
    return PlainTextResponse("\n".join(lines), media_type="text/plain")
