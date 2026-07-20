"""Add trusted medical RAG pipeline.

Revision ID: 20260712_05
Revises: 20260712_04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260712_05"
down_revision: str | None = "20260712_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("publisher", sa.String(180), nullable=False),
        sa.Column("base_url", sa.String(2048), nullable=False),
        sa.Column("approval_status", sa.String(24), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("freshness_days", sa.Integer(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_knowledge_sources_approval_status", "knowledge_sources", ["approval_status"]
    )
    op.create_index(
        "ix_knowledge_sources_status_review",
        "knowledge_sources",
        ["approval_status", "last_reviewed_at"],
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_knowledge_documents_source_id", "knowledge_documents", ["source_id"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])
    op.create_index(
        "ix_knowledge_documents_source_status",
        "knowledge_documents",
        ["source_id", "status"],
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])
    op.create_index(
        "ix_knowledge_chunks_document_order", "knowledge_chunks", ["document_id", "chunk_index"]
    )
    op.create_table(
        "retrieval_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("top_score", sa.Float(), nullable=False),
        sa.Column("no_answer", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retrieval_logs_user_id", "retrieval_logs", ["user_id"])
    op.create_index("ix_retrieval_logs_conversation_id", "retrieval_logs", ["conversation_id"])


def downgrade() -> None:
    op.drop_table("retrieval_logs")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("knowledge_sources")
