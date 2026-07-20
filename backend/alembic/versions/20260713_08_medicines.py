"""Add verified medicine information module.

Revision ID: 20260713_08
Revises: 20260713_07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_08"
down_revision: str | None = "20260713_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medicine_search_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.String(160), nullable=False),
        sa.Column("normalized_query", sa.String(160), nullable=False),
        sa.Column("matched_generic_name", sa.String(160), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medicine_search_history_user_id", "medicine_search_history", ["user_id"])
    op.create_index(
        "ix_medicine_search_history_normalized_query",
        "medicine_search_history",
        ["normalized_query"],
    )
    op.create_index(
        "ix_medicine_search_history_user_recent",
        "medicine_search_history",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("medicine_search_history")
