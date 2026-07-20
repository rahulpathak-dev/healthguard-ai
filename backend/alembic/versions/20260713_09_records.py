"""Add secure medical record file management.

Revision ID: 20260713_09
Revises: 20260713_08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260713_09"
down_revision: str | None = "20260713_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("medical_records", sa.Column("owner_user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "medical_records",
        sa.Column("original_filename", sa.String(220), nullable=False, server_default=""),
    )
    op.add_column(
        "medical_records",
        sa.Column(
            "mime_type", sa.String(120), nullable=False, server_default="application/octet-stream"
        ),
    )
    op.add_column(
        "medical_records",
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "medical_records",
        sa.Column("storage_path", sa.String(500), nullable=False, server_default=""),
    )
    op.add_column(
        "medical_records", sa.Column("sha256", sa.String(64), nullable=False, server_default="")
    )
    op.add_column(
        "medical_records",
        sa.Column("status", sa.String(24), nullable=False, server_default="quarantined"),
    )
    op.add_column(
        "medical_records",
        sa.Column("scan_status", sa.String(24), nullable=False, server_default="pending"),
    )
    op.add_column(
        "medical_records", sa.Column("tags_json", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "medical_records",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "medical_records", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "medical_records", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE medical_records AS record SET owner_user_id = profile.owner_user_id "
        "FROM health_profiles AS profile WHERE profile.id = record.profile_id"
    )
    op.alter_column("medical_records", "owner_user_id", nullable=False)
    op.create_foreign_key(
        "fk_medical_records_owner",
        "medical_records",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_medical_records_owner_user_id", "medical_records", ["owner_user_id"])
    op.create_index("ix_medical_records_status", "medical_records", ["status"])
    op.create_index("ix_medical_records_scan_status", "medical_records", ["scan_status"])
    op.create_index(
        "ix_medical_records_profile_status",
        "medical_records",
        ["profile_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_medical_records_profile_status", table_name="medical_records")
    op.drop_index("ix_medical_records_scan_status", table_name="medical_records")
    op.drop_index("ix_medical_records_status", table_name="medical_records")
    op.drop_index("ix_medical_records_owner_user_id", table_name="medical_records")
    op.drop_constraint("fk_medical_records_owner", "medical_records", type_="foreignkey")
    op.drop_column("medical_records", "deleted_at")
    op.drop_column("medical_records", "archived_at")
    op.drop_column("medical_records", "metadata_json")
    op.drop_column("medical_records", "tags_json")
    op.drop_column("medical_records", "scan_status")
    op.drop_column("medical_records", "status")
    op.drop_column("medical_records", "sha256")
    op.drop_column("medical_records", "storage_path")
    op.drop_column("medical_records", "file_size_bytes")
    op.drop_column("medical_records", "mime_type")
    op.drop_column("medical_records", "original_filename")
    op.drop_column("medical_records", "owner_user_id")
