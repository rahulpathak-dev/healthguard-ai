"""Add misinformation checker history and feedback.

Revision ID: 20260713_12
Revises: 20260713_11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_12"
down_revision: str | None = "20260713_11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "misinformation_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("claim_hash", sa.String(64), nullable=False),
        sa.Column("claim_summary", sa.String(500), nullable=False),
        sa.Column("verdict", sa.String(40), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_misinformation_checks_user_id", "misinformation_checks", ["user_id"])
    op.create_index("ix_misinformation_checks_claim_hash", "misinformation_checks", ["claim_hash"])
    op.create_index("ix_misinformation_checks_verdict", "misinformation_checks", ["verdict"])
    op.create_index(
        "ix_misinformation_checks_user_created", "misinformation_checks", ["user_id", "created_at"]
    )
    op.create_table(
        "misinformation_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("check_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.String(24), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["check_id"], ["misinformation_checks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_misinformation_feedback_check_id", "misinformation_feedback", ["check_id"])
    op.create_index("ix_misinformation_feedback_user_id", "misinformation_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_table("misinformation_feedback")
    op.drop_table("misinformation_checks")
