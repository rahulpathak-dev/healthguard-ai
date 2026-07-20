import uuid
from datetime import datetime

from pydantic import BaseModel


class ProfileOption(BaseModel):
    id: uuid.UUID
    display_name: str
    kind: str
    relationship: str | None
    is_owner: bool
    can_edit: bool


class ReminderSummary(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    due_at: datetime


class RecordSummary(BaseModel):
    id: uuid.UUID
    title: str
    record_type: str
    occurred_at: datetime | None
    created_at: datetime


class AnalysisSummary(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str
    last_message_at: datetime


class NotificationSummary(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    created_at: datetime


class FamilySummary(BaseModel):
    id: uuid.UUID
    display_name: str
    relationship: str | None
    age: int | None


class PrivacySummary(BaseModel):
    access_label: str
    permission_count: int
    doctor_sharing_enabled: bool
    family_sharing_enabled: bool


class EducationCard(BaseModel):
    slug: str
    title: str
    description: str
    reading_minutes: int


class QuickAction(BaseModel):
    label: str
    href: str
    available: bool


class EmergencyShortcut(BaseModel):
    label: str
    description: str
    action: str


class DashboardView(BaseModel):
    welcome_name: str
    profiles: list[ProfileOption]
    active_profile: ProfileOption | None
    upcoming_reminders: list[ReminderSummary]
    recent_records: list[RecordSummary]
    report_analyses: list[AnalysisSummary]
    recent_conversations: list[ConversationSummary]
    notifications: list[NotificationSummary]
    unread_notification_count: int
    family: list[FamilySummary]
    privacy: PrivacySummary | None
    education: list[EducationCard]
    quick_actions: list[QuickAction]
    emergency_shortcuts: list[EmergencyShortcut]
