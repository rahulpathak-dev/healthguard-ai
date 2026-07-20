"""Add consent-based doctor sharing and admin governance."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "20260713_13"
down_revision = "20260713_12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "doctor_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("specialty", sa.String(length=120), nullable=True),
        sa.Column("license_region", sa.String(length=80), nullable=True),
        sa.Column("verification_status", sa.String(length=24), nullable=False),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_doctor_profiles_user_id"), "doctor_profiles", ["user_id"])
    op.create_index(
        op.f("ix_doctor_profiles_verification_status"),
        "doctor_profiles",
        ["verification_status"],
    )
    op.create_table(
        "record_share_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("doctor_user_id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=24), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_record_share_grants_doctor_active",
        "record_share_grants",
        ["doctor_user_id", "revoked_at", "expires_at"],
    )
    op.create_index(
        "ix_record_share_grants_owner_created",
        "record_share_grants",
        ["owner_user_id", "created_at"],
    )
    op.create_index(
        op.f("ix_record_share_grants_doctor_user_id"), "record_share_grants", ["doctor_user_id"]
    )
    op.create_index(
        op.f("ix_record_share_grants_expires_at"), "record_share_grants", ["expires_at"]
    )
    op.create_index(
        op.f("ix_record_share_grants_owner_user_id"), "record_share_grants", ["owner_user_id"]
    )
    op.create_index(
        op.f("ix_record_share_grants_profile_id"), "record_share_grants", ["profile_id"]
    )
    op.create_index(
        op.f("ix_record_share_grants_revoked_at"), "record_share_grants", ["revoked_at"]
    )
    op.create_table(
        "record_share_grant_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("grant_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["grant_id"], ["record_share_grants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_record_share_grant_items_grant_id"), "record_share_grant_items", ["grant_id"]
    )
    op.create_index(
        op.f("ix_record_share_grant_items_record_id"), "record_share_grant_items", ["record_id"]
    )
    op.create_index(
        "uq_grant_record", "record_share_grant_items", ["grant_id", "record_id"], unique=True
    )
    op.create_table(
        "doctor_review_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("grant_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("doctor_user_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grant_id"], ["record_share_grants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_doctor_review_notes_doctor_user_id"), "doctor_review_notes", ["doctor_user_id"]
    )
    op.create_index(op.f("ix_doctor_review_notes_grant_id"), "doctor_review_notes", ["grant_id"])
    op.create_index(
        op.f("ix_doctor_review_notes_owner_user_id"), "doctor_review_notes", ["owner_user_id"]
    )
    op.create_index(op.f("ix_doctor_review_notes_record_id"), "doctor_review_notes", ["record_id"])
    op.create_table(
        "record_access_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("grant_id", sa.Uuid(), nullable=True),
        sa.Column("record_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grant_id"], ["record_share_grants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_record_access_audit_logs_action"), "record_access_audit_logs", ["action"]
    )
    op.create_index(
        op.f("ix_record_access_audit_logs_actor_user_id"),
        "record_access_audit_logs",
        ["actor_user_id"],
    )
    op.create_index(
        op.f("ix_record_access_audit_logs_created_at"), "record_access_audit_logs", ["created_at"]
    )
    op.create_index(
        op.f("ix_record_access_audit_logs_grant_id"), "record_access_audit_logs", ["grant_id"]
    )
    op.create_index(
        op.f("ix_record_access_audit_logs_owner_user_id"),
        "record_access_audit_logs",
        ["owner_user_id"],
    )
    op.create_index(
        op.f("ix_record_access_audit_logs_record_id"), "record_access_audit_logs", ["record_id"]
    )
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("admin_user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=80), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_audit_logs_action"), "admin_audit_logs", ["action"])
    op.create_index(
        op.f("ix_admin_audit_logs_admin_user_id"), "admin_audit_logs", ["admin_user_id"]
    )
    op.create_index(op.f("ix_admin_audit_logs_created_at"), "admin_audit_logs", ["created_at"])
    op.create_index(op.f("ix_admin_audit_logs_target_id"), "admin_audit_logs", ["target_id"])
    op.create_index(op.f("ix_admin_audit_logs_target_type"), "admin_audit_logs", ["target_type"])
    op.create_index(
        "ix_admin_audit_target", "admin_audit_logs", ["target_type", "target_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_target", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_table("record_access_audit_logs")
    op.drop_table("doctor_review_notes")
    op.drop_index("uq_grant_record", table_name="record_share_grant_items")
    op.drop_table("record_share_grant_items")
    op.drop_table("record_share_grants")
    op.drop_table("doctor_profiles")
