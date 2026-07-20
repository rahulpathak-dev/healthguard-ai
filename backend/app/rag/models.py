import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(180), unique=True)
    publisher: Mapped[str] = mapped_column(String(180))
    base_url: Mapped[str] = mapped_column(String(2048))
    approval_status: Mapped[str] = mapped_column(String(24), index=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    freshness_days: Mapped[int] = mapped_column(Integer, default=365)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index("ix_knowledge_sources_status_review", "approval_status", "last_reviewed_at"),
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    normalized_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    __table_args__ = (Index("ix_knowledge_documents_source_status", "source_id", "status"),)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(JSON)
    token_count: Mapped[int] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    __table_args__ = (Index("ix_knowledge_chunks_document_order", "document_id", "chunk_index"),)


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="SET NULL"), index=True
    )
    query: Mapped[str] = mapped_column(String(500))
    filters_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    result_count: Mapped[int] = mapped_column(Integer)
    top_score: Mapped[float] = mapped_column(Float, default=0)
    no_answer: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
