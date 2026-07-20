"""Add centralized medical AI safety engine.

Revision ID: 20260713_06
Revises: 20260712_05
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_06"
down_revision: str | None = "20260712_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_safety_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(24), nullable=False),
        sa.Column("categories_json", sa.JSON(), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_safety_events_user_id", "ai_safety_events", ["user_id"])
    op.create_index("ix_ai_safety_events_conversation_id", "ai_safety_events", ["conversation_id"])
    op.create_index("ix_ai_safety_events_message_id", "ai_safety_events", ["message_id"])
    op.create_index("ix_ai_safety_events_severity", "ai_safety_events", ["severity"])
    op.create_index(
        "ix_ai_safety_events_stage_created", "ai_safety_events", ["stage", "created_at"]
    )
    op.create_table(
        "ai_safety_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_safety_reports_user_id", "ai_safety_reports", ["user_id"])
    op.create_index("ix_ai_safety_reports_message_id", "ai_safety_reports", ["message_id"])
    op.create_index("ix_ai_safety_reports_status", "ai_safety_reports", ["status"])


def downgrade() -> None:
    op.drop_table("ai_safety_reports")
    op.drop_table("ai_safety_events")
