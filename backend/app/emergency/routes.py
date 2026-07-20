from fastapi import APIRouter

from app.core.config import get_settings
from app.core.responses import ApiResponse
from app.emergency.content import TOPICS
from app.emergency.schemas import EmergencyConfig, EmergencyTopic

router = APIRouter()


@router.get("", response_model=ApiResponse[EmergencyConfig])
async def guidance() -> ApiResponse[EmergencyConfig]:
    settings = get_settings()
    return ApiResponse(
        data=EmergencyConfig(
            emergency_number=settings.emergency_number,
            country_hint=settings.emergency_country_hint,
            disclaimer=(
                "This is first-aid education. Call local emergency services for urgent "
                "or life-threatening symptoms."
            ),
            topics=list(TOPICS),
        )
    )


@router.get("/{slug}", response_model=ApiResponse[EmergencyTopic])
async def topic(slug: str) -> ApiResponse[EmergencyTopic]:
    item = next((entry for entry in TOPICS if entry.slug == slug), TOPICS[0])
    return ApiResponse(data=item)
