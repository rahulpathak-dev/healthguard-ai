"""Add dashboard summary sources.

Revision ID: 20260712_03
Revises: 20260711_02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260712_03"
down_revision: str | None = "20260711_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "health_reminders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_reminders_profile_id", "health_reminders", ["profile_id"])
    op.create_index(
        "ix_health_reminders_profile_due", "health_reminders", ["profile_id", "status", "due_at"]
    )
    op.create_table(
        "medical_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("record_type", sa.String(50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medical_records_profile_id", "medical_records", ["profile_id"])
    op.create_index(
        "ix_medical_records_profile_created", "medical_records", ["profile_id", "created_at"]
    )
    op.create_table(
        "report_analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_analyses_profile_id", "report_analyses", ["profile_id"])
    op.create_index(
        "ix_report_analyses_profile_created", "report_analyses", ["profile_id", "created_at"]
    )
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_profile_id", "ai_conversations", ["profile_id"])
    op.create_index(
        "ix_ai_conversations_profile_recent", "ai_conversations", ["profile_id", "last_message_at"]
    )
    op.create_table(
        "user_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_notifications_user_id", "user_notifications", ["user_id"])
    op.create_index(
        "ix_user_notifications_unread", "user_notifications", ["user_id", "read_at", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("user_notifications")
    op.drop_table("ai_conversations")
    op.drop_table("report_analyses")
    op.drop_table("medical_records")
    op.drop_table("health_reminders")
