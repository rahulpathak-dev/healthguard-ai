import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReminderCategory = Literal[
    "doctor_appointment",
    "medicine_schedule",
    "vaccination",
    "health_check",
    "test",
    "follow_up",
    "other",
]
Recurrence = Literal["none", "daily", "weekly", "monthly"]


class ReminderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    profile_id: uuid.UUID
    title: str = Field(min_length=1, max_length=180)
    category: ReminderCategory
    due_at: datetime
    timezone: str = Field(default="UTC", max_length=64)
    recurrence: Recurrence = "none"
    notes: str | None = Field(default=None, max_length=500)


class ReminderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=180)
    due_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    recurrence: Recurrence | None = None
    notes: str | None = Field(default=None, max_length=500)


class ReminderView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    profile_id: uuid.UUID
    owner_user_id: uuid.UUID
    title: str
    category: str
    due_at: datetime
    timezone: str
    recurrence_rule: str
    status: str
    notes: str | None
    completed_at: datetime | None
    snoozed_until: datetime | None


class PreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    channel: Literal["in_app", "email", "sms", "push"]
    enabled: bool


class DeliveryLogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reminder_id: uuid.UUID
    channel: str
    status: str
    provider_message: str | None
    attempted_at: datetime
