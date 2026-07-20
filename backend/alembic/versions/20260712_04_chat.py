"""Add secure health education chat.

Revision ID: 20260712_04
Revises: 20260712_03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260712_04"
down_revision: str | None = "20260712_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_conversations", sa.Column("owner_user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "ai_conversations",
        sa.Column("language", sa.String(16), server_default="en", nullable=False),
    )
    op.add_column("ai_conversations", sa.Column("created_at", sa.DateTime(timezone=True)))
    op.execute(
        "UPDATE ai_conversations AS conversation "
        "SET owner_user_id = profile.owner_user_id, created_at = conversation.last_message_at "
        "FROM health_profiles AS profile WHERE profile.id = conversation.profile_id"
    )
    op.alter_column("ai_conversations", "owner_user_id", nullable=False)
    op.alter_column("ai_conversations", "created_at", nullable=False)
    op.create_foreign_key(
        "fk_ai_conversations_owner",
        "ai_conversations",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_ai_conversations_owner_user_id", "ai_conversations", ["owner_user_id"])
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("parent_message_id", sa.Uuid(), nullable=True),
        sa.Column("estimated_tokens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_message_id"], ["chat_messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "sequence", name="uq_chat_message_sequence"),
    )
    op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])
    op.create_index(
        "ix_chat_messages_conversation_recent", "chat_messages", ["conversation_id", "sequence"]
    )
    op.create_table(
        "chat_citations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("excerpt", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_citations_message_id", "chat_citations", ["message_id"])
    op.create_table(
        "chat_message_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_chat_feedback_user"),
    )
    op.create_index("ix_chat_message_feedback_message_id", "chat_message_feedback", ["message_id"])
    op.create_index("ix_chat_message_feedback_user_id", "chat_message_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_table("chat_message_feedback")
    op.drop_table("chat_citations")
    op.drop_table("chat_messages")
    op.drop_index("ix_ai_conversations_owner_user_id", table_name="ai_conversations")
    op.drop_constraint("fk_ai_conversations_owner", "ai_conversations", type_="foreignkey")
    op.drop_column("ai_conversations", "created_at")
    op.drop_column("ai_conversations", "language")
    op.drop_column("ai_conversations", "owner_user_id")
