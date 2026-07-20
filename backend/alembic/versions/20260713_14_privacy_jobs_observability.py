"""Add privacy controls jobs caching and observability."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "20260713_14"
down_revision = "20260713_13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("queue", sa.String(length=40), nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    for column in [
        "queue",
        "job_type",
        "status",
        "idempotency_key",
        "owner_user_id",
        "locked_until",
        "scheduled_at",
    ]:
        op.create_index(op.f(f"ix_background_jobs_{column}"), "background_jobs", [column])
    op.create_index(
        "ix_background_jobs_queue_status", "background_jobs", ["queue", "status", "scheduled_at"]
    )
    op.create_index(
        "ix_background_jobs_owner_created", "background_jobs", ["owner_user_id", "created_at"]
    )
    op.create_table(
        "cache_invalidation_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cache_key", sa.String(length=240), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cache_invalidation_logs_cache_key"), "cache_invalidation_logs", ["cache_key"]
    )
    op.create_table(
        "consent_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("subject_type", sa.String(length=60), nullable=False),
        sa.Column("subject_id", sa.String(length=80), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["user_id", "event_type", "action", "created_at"]:
        op.create_index(op.f(f"ix_consent_events_{column}"), "consent_events", [column])
    op.create_index("ix_consent_events_user_created", "consent_events", ["user_id", "created_at"])
    op.create_table(
        "data_export_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("export_path", sa.String(length=500), nullable=True),
        sa.Column("download_token_hash", sa.String(length=64), nullable=True),
        sa.Column("download_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["background_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["user_id", "job_id", "status", "download_token_hash", "download_expires_at"]:
        op.create_index(op.f(f"ix_data_export_requests_{column}"), "data_export_requests", [column])
    op.create_table(
        "account_deletion_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("confirmation_phrase_hash", sa.String(length=64), nullable=False),
        sa.Column("grace_period_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["background_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["user_id", "job_id", "status", "grace_period_ends_at"]:
        op.create_index(
            op.f(f"ix_account_deletion_requests_{column}"), "account_deletion_requests", [column]
        )
    op.create_table(
        "privacy_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("cookie_preferences_json", sa.JSON(), nullable=False),
        sa.Column("notification_preferences_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_privacy_preferences_user_id"), "privacy_preferences", ["user_id"])


def downgrade() -> None:
    op.drop_table("privacy_preferences")
    op.drop_table("account_deletion_requests")
    op.drop_table("data_export_requests")
    op.drop_table("consent_events")
    op.drop_table("cache_invalidation_logs")
    op.drop_table("background_jobs")
