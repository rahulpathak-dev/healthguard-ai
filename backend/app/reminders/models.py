import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(24))
    enabled: Mapped[bool] = mapped_column(default=True)
    quiet_hours_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_notification_preferences_user_channel", "user_id", "channel"),)


class ReminderDeliveryLog(Base):
    __tablename__ = "reminder_delivery_logs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    reminder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_reminders.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24))
    provider_message: Mapped[str | None] = mapped_column(String(300))
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
