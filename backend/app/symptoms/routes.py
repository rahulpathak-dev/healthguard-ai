import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.db.session import get_db_session
from app.profiles.service import get_accessible_profile
from app.symptoms.models import SymptomAssessment
from app.symptoms.schemas import SymptomAssessmentCreate, SymptomAssessmentView
from app.symptoms.service import build_assessment, owned_assessment

router = APIRouter()


@router.post("/assessments", response_model=ApiResponse[SymptomAssessmentView], status_code=201)
async def create_assessment(
    payload: SymptomAssessmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SymptomAssessmentView]:
    await get_accessible_profile(db, payload.profile_id, user.id, require_edit=True)
    assessment = await build_assessment(db, user=user, payload=payload)
    await db.commit()
    return ApiResponse(data=SymptomAssessmentView.model_validate(assessment))


@router.get("/assessments", response_model=ApiResponse[list[SymptomAssessmentView]])
async def list_assessments(
    profile_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[SymptomAssessmentView]]:
    await get_accessible_profile(db, profile_id, user.id)
    rows = (
        await db.scalars(
            select(SymptomAssessment)
            .where(
                SymptomAssessment.profile_id == profile_id,
                SymptomAssessment.owner_user_id == user.id,
            )
            .order_by(SymptomAssessment.created_at.desc())
            .limit(limit)
        )
    ).all()
    return ApiResponse(data=[SymptomAssessmentView.model_validate(row) for row in rows])


@router.get("/assessments/{assessment_id}", response_model=ApiResponse[SymptomAssessmentView])
async def get_assessment(
    assessment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SymptomAssessmentView]:
    assessment = await owned_assessment(db, assessment_id, user.id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return ApiResponse(data=SymptomAssessmentView.model_validate(assessment))
