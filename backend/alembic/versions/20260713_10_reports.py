"""Add OCR report explanation fields.

Revision ID: 20260713_10
Revises: 20260713_09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_10"
down_revision: str | None = "20260713_09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("report_analyses", sa.Column("owner_user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "report_analyses",
        sa.Column("ocr_status", sa.String(40), nullable=False, server_default="queued"),
    )
    op.add_column("report_analyses", sa.Column("ocr_confidence", sa.Float(), nullable=True))
    op.add_column(
        "report_analyses",
        sa.Column("extracted_values_json", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "report_analyses",
        sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column("report_analyses", sa.Column("error_message", sa.String(500), nullable=True))
    op.add_column(
        "report_analyses", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE report_analyses AS analysis SET owner_user_id = profile.owner_user_id "
        "FROM health_profiles AS profile WHERE profile.id = analysis.profile_id"
    )
    op.alter_column("report_analyses", "owner_user_id", nullable=False)
    op.create_foreign_key(
        "fk_report_analyses_owner",
        "report_analyses",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_report_analyses_owner_user_id", "report_analyses", ["owner_user_id"])
    op.create_index(
        "ix_report_analyses_owner_created", "report_analyses", ["owner_user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_report_analyses_owner_created", table_name="report_analyses")
    op.drop_index("ix_report_analyses_owner_user_id", table_name="report_analyses")
    op.drop_constraint("fk_report_analyses_owner", "report_analyses", type_="foreignkey")
    op.drop_column("report_analyses", "completed_at")
    op.drop_column("report_analyses", "error_message")
    op.drop_column("report_analyses", "explanation_json")
    op.drop_column("report_analyses", "extracted_values_json")
    op.drop_column("report_analyses", "ocr_confidence")
    op.drop_column("report_analyses", "ocr_status")
    op.drop_column("report_analyses", "owner_user_id")
