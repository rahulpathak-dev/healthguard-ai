import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dashboard.models import Notification, Reminder
from app.profiles.service import get_accessible_profile
from app.reminders.models import ReminderDeliveryLog
from app.reminders.schemas import ReminderCreate, ReminderUpdate


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Invalid timezone") from exc
    return value


def next_due(due_at: datetime, recurrence: str) -> datetime | None:
    if recurrence == "daily":
        return due_at + timedelta(days=1)
    if recurrence == "weekly":
        return due_at + timedelta(weeks=1)
    if recurrence == "monthly":
        return due_at + timedelta(days=30)
    return None


def unsafe_medicine_wording(title: str, category: str) -> bool:
    lowered = title.lower()
    return category == "medicine_schedule" and any(
        term in lowered for term in ("increase dose", "double dose", "stop medicine")
    )


async def create_reminder(db: AsyncSession, *, user: User, payload: ReminderCreate) -> Reminder:
    await get_accessible_profile(db, payload.profile_id, user.id, require_edit=True)
    if unsafe_medicine_wording(payload.title, payload.category):
        raise HTTPException(status_code=422, detail="Unsafe medicine reminder wording")
    reminder = Reminder(
        profile_id=payload.profile_id,
        owner_user_id=user.id,
        title=payload.title,
        category=payload.category,
        due_at=payload.due_at.astimezone(UTC),
        timezone=validate_timezone(payload.timezone),
        recurrence_rule=payload.recurrence,
        status="pending",
        notes=payload.notes,
    )
    db.add(reminder)
    await db.flush()
    return reminder


async def owned_reminder(db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID) -> Reminder:
    reminder = await db.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.owner_user_id == user_id)
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


async def update_reminder(reminder: Reminder, payload: ReminderUpdate) -> Reminder:
    if payload.title is not None:
        reminder.title = payload.title
    if payload.due_at is not None:
        reminder.due_at = payload.due_at.astimezone(UTC)
    if payload.timezone is not None:
        reminder.timezone = validate_timezone(payload.timezone)
    if payload.recurrence is not None:
        reminder.recurrence_rule = payload.recurrence
    if payload.notes is not None:
        reminder.notes = payload.notes
    if unsafe_medicine_wording(reminder.title, reminder.category):
        raise HTTPException(status_code=422, detail="Unsafe medicine reminder wording")
    return reminder


async def complete_reminder(db: AsyncSession, reminder: Reminder) -> Reminder:
    reminder.completed_at = datetime.now(UTC)
    next_time = next_due(reminder.due_at, reminder.recurrence_rule)
    if next_time:
        reminder.due_at = next_time
        reminder.status = "pending"
        reminder.completed_at = None
    else:
        reminder.status = "complete"
    db.add(
        Notification(
            user_id=reminder.owner_user_id,
            profile_id=reminder.profile_id,
            title=f"Completed: {reminder.title}",
            category="reminder",
            created_at=datetime.now(UTC),
            read_at=None,
        )
    )
    return reminder


async def log_delivery(
    db: AsyncSession, *, reminder: Reminder, channel: str, status: str, provider_message: str | None
) -> ReminderDeliveryLog:
    log = ReminderDeliveryLog(
        reminder_id=reminder.id,
        user_id=reminder.owner_user_id,
        channel=channel,
        status=status,
        provider_message=provider_message,
        attempted_at=datetime.now(UTC),
    )
    db.add(log)
    return log
