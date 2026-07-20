import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.responses import ApiResponse
from app.dashboard.models import Notification, Reminder
from app.db.session import get_db_session
from app.reminders.models import NotificationPreference
from app.reminders.schemas import (
    DeliveryLogView,
    PreferenceUpdate,
    ReminderCreate,
    ReminderUpdate,
    ReminderView,
)
from app.reminders.service import (
    complete_reminder,
    create_reminder,
    log_delivery,
    owned_reminder,
    update_reminder,
)

router = APIRouter()


@router.post("", response_model=ApiResponse[ReminderView], status_code=201)
async def create(
    payload: ReminderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReminderView]:
    reminder = await create_reminder(db, user=user, payload=payload)
    await db.commit()
    return ApiResponse(data=ReminderView.model_validate(reminder))


@router.get("", response_model=ApiResponse[list[ReminderView]])
async def list_items(
    profile_id: uuid.UUID | None = None,
    include_complete: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[ReminderView]]:
    statement = select(Reminder).where(Reminder.owner_user_id == user.id)
    if profile_id:
        statement = statement.where(Reminder.profile_id == profile_id)
    if not include_complete:
        statement = statement.where(Reminder.status != "complete")
    rows = (await db.scalars(statement.order_by(Reminder.due_at).limit(100))).all()
    return ApiResponse(data=[ReminderView.model_validate(row) for row in rows])


@router.patch("/{reminder_id}", response_model=ApiResponse[ReminderView])
async def update(
    reminder_id: uuid.UUID,
    payload: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReminderView]:
    reminder = await owned_reminder(db, reminder_id, user.id)
    await update_reminder(reminder, payload)
    await db.commit()
    return ApiResponse(data=ReminderView.model_validate(reminder))


@router.post("/{reminder_id}/snooze", response_model=ApiResponse[ReminderView])
async def snooze(
    reminder_id: uuid.UUID,
    minutes: int = Query(default=30, ge=5, le=1440),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReminderView]:
    reminder = await owned_reminder(db, reminder_id, user.id)
    reminder.snoozed_until = datetime.now(UTC) + timedelta(minutes=minutes)
    await db.commit()
    return ApiResponse(data=ReminderView.model_validate(reminder))


@router.post("/{reminder_id}/complete", response_model=ApiResponse[ReminderView])
async def complete(
    reminder_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReminderView]:
    reminder = await owned_reminder(db, reminder_id, user.id)
    await complete_reminder(db, reminder)
    await db.commit()
    return ApiResponse(data=ReminderView.model_validate(reminder))


@router.post("/{reminder_id}/delivery-log", response_model=ApiResponse[DeliveryLogView])
async def delivery_log(
    reminder_id: uuid.UUID,
    channel: str = Query(pattern="^(in_app|email|sms|push)$"),
    status: str = Query(pattern="^(queued|sent|failed|skipped)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DeliveryLogView]:
    reminder = await owned_reminder(db, reminder_id, user.id)
    log = await log_delivery(
        db, reminder=reminder, channel=channel, status=status, provider_message=None
    )
    await db.commit()
    return ApiResponse(data=DeliveryLogView.model_validate(log))


@router.put("/preferences", status_code=204)
async def preference(
    payload: PreferenceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    existing = await db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.channel == payload.channel,
        )
    )
    if existing:
        existing.enabled = payload.enabled
        existing.updated_at = datetime.now(UTC)
    else:
        db.add(
            NotificationPreference(
                user_id=user.id,
                channel=payload.channel,
                enabled=payload.enabled,
                quiet_hours_json={},
                updated_at=datetime.now(UTC),
            )
        )
    await db.commit()


@router.get("/notifications", response_model=ApiResponse[list[dict[str, object]]])
async def notifications(
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[list[dict[str, object]]]:
    statement = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        statement = statement.where(Notification.read_at.is_(None))
    rows = (await db.scalars(statement.order_by(Notification.created_at.desc()).limit(50))).all()
    return ApiResponse(
        data=[
            {
                "id": str(row.id),
                "profile_id": str(row.profile_id) if row.profile_id else None,
                "title": row.title,
                "category": row.category,
                "created_at": row.created_at.isoformat(),
                "read_at": row.read_at.isoformat() if row.read_at else None,
            }
            for row in rows
        ]
    )


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    notification = await db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification:
        notification.read_at = datetime.now(UTC)
        await db.commit()
