"""Add personal and family health profiles.

Revision ID: 20260711_02
Revises: 20260711_01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260711_02"
down_revision: str | None = "20260711_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    profile_kind = sa.Enum("PERSONAL", "FAMILY", name="profilekind")
    permission_level = sa.Enum("VIEW", "EDIT", name="permissionlevel")
    profile_kind.create(op.get_bind(), checkfirst=True)
    permission_level.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "health_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", profile_kind, nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False),
        sa.Column("relationship", sa.String(80), nullable=True),
        sa.Column("dedupe_key", sa.String(64), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("blood_group", sa.String(3), nullable=True),
        sa.Column("sex_at_birth", sa.String(40), nullable=True),
        sa.Column("gender_identity", sa.String(80), nullable=True),
        sa.Column("pronouns", sa.String(40), nullable=True),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("locale", sa.String(20), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("allow_doctor_access", sa.Boolean(), nullable=False),
        sa.Column("share_with_family", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "dedupe_key", name="uq_profile_owner_dedupe"),
    )
    op.create_index("ix_health_profiles_owner_user_id", "health_profiles", ["owner_user_id"])
    op.create_index("ix_health_profiles_kind", "health_profiles", ["kind"])
    op.create_index(
        "uq_personal_profile_owner",
        "health_profiles",
        ["owner_user_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'PERSONAL'"),
    )
    op.create_table(
        "profile_emergency_contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("relationship", sa.String(80), nullable=True),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_emergency_contacts_profile_id", "profile_emergency_contacts", ["profile_id"]
    )
    op.create_table(
        "profile_allergies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("substance", sa.String(160), nullable=False),
        sa.Column("reaction_summary", sa.String(500), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profile_allergies_profile_id", "profile_allergies", ["profile_id"])
    op.create_table(
        "profile_current_medicines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("dosage", sa.String(120), nullable=True),
        sa.Column("schedule", sa.String(160), nullable=True),
        sa.Column("reason", sa.String(300), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_current_medicines_profile_id", "profile_current_medicines", ["profile_id"]
    )
    op.create_table(
        "profile_chronic_conditions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("summary", sa.String(1000), nullable=True),
        sa.Column("diagnosed_on", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_chronic_conditions_profile_id", "profile_chronic_conditions", ["profile_id"]
    )
    op.create_table(
        "profile_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("grantee_user_id", sa.Uuid(), nullable=False),
        sa.Column("level", permission_level, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["health_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grantee_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "grantee_user_id", name="uq_profile_grantee"),
    )
    op.create_index("ix_profile_permissions_profile_id", "profile_permissions", ["profile_id"])
    op.create_index(
        "ix_profile_permissions_grantee_user_id", "profile_permissions", ["grantee_user_id"]
    )


def downgrade() -> None:
    op.drop_table("profile_permissions")
    op.drop_table("profile_chronic_conditions")
    op.drop_table("profile_current_medicines")
    op.drop_table("profile_allergies")
    op.drop_table("profile_emergency_contacts")
    op.drop_table("health_profiles")
    sa.Enum(name="permissionlevel").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="profilekind").drop(op.get_bind(), checkfirst=True)
