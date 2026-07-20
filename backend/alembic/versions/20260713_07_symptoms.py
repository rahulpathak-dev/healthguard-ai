"""Add non-diagnostic symptom guidance assistant.

Revision ID: 20260713_07
Revises: 20260713_06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_07"
down_revision: str | None = "20260713_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "symptom_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("symptoms_json", sa.JSON(), nullable=False),
        sa.Column("duration", sa.String(120), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("age_group", sa.String(40), nullable=False),
        sa.Column("relevant_context", sa.Text(), nullable=True),
        sa.Column("associated_symptoms_json", sa.JSON(), nullable=False),
        sa.Column("warning_signs_json", sa.JSON(), nullable=False),
        sa.Column("urgency_level", sa.String(40), nullable=False),
        sa.Column("red_flags_json", sa.JSON(), nullable=False),
        sa.Column("guidance_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_symptom_assessments_profile_id", "symptom_assessments", ["profile_id"])
    op.create_index(
        "ix_symptom_assessments_owner_user_id", "symptom_assessments", ["owner_user_id"]
    )
    op.create_index(
        "ix_symptom_assessments_urgency_level", "symptom_assessments", ["urgency_level"]
    )
    op.create_index(
        "ix_symptom_assessments_profile_created",
        "symptom_assessments",
        ["profile_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("symptom_assessments")
