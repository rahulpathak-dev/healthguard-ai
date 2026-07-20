"""Add reminders and notification center.

Revision ID: 20260713_11
Revises: 20260713_10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_11"
down_revision: str | None = "20260713_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("health_reminders", sa.Column("owner_user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "health_reminders",
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
    )
    op.add_column(
        "health_reminders",
        sa.Column("recurrence_rule", sa.String(24), nullable=False, server_default="none"),
    )
    op.add_column("health_reminders", sa.Column("notes", sa.String(500), nullable=True))
    op.add_column(
        "health_reminders", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "health_reminders", sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE health_reminders AS reminder SET owner_user_id = profile.owner_user_id "
        "FROM health_profiles AS profile WHERE profile.id = reminder.profile_id"
    )
    op.alter_column("health_reminders", "owner_user_id", nullable=False)
    op.create_foreign_key(
        "fk_health_reminders_owner",
        "health_reminders",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_health_reminders_owner_user_id", "health_reminders", ["owner_user_id"])
    op.create_index(
        "ix_health_reminders_owner_due", "health_reminders", ["owner_user_id", "status", "due_at"]
    )
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("quiet_hours_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])
    op.create_index(
        "ix_notification_preferences_user_channel",
        "notification_preferences",
        ["user_id", "channel"],
    )
    op.create_table(
        "reminder_delivery_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reminder_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("provider_message", sa.String(300), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reminder_id"], ["health_reminders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reminder_delivery_logs_reminder_id", "reminder_delivery_logs", ["reminder_id"]
    )
    op.create_index("ix_reminder_delivery_logs_user_id", "reminder_delivery_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("reminder_delivery_logs")
    op.drop_table("notification_preferences")
    op.drop_index("ix_health_reminders_owner_due", table_name="health_reminders")
    op.drop_index("ix_health_reminders_owner_user_id", table_name="health_reminders")
    op.drop_constraint("fk_health_reminders_owner", "health_reminders", type_="foreignkey")
    op.drop_column("health_reminders", "snoozed_until")
    op.drop_column("health_reminders", "completed_at")
    op.drop_column("health_reminders", "notes")
    op.drop_column("health_reminders", "recurrence_rule")
    op.drop_column("health_reminders", "timezone")
    op.drop_column("health_reminders", "owner_user_id")
