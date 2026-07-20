import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(20), default="complete")
    sequence: Mapped[int] = mapped_column(Integer)
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="SET NULL")
    )
    estimated_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    citations: Mapped[list["ChatCitation"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("conversation_id", "sequence", name="uq_chat_message_sequence"),
        Index("ix_chat_messages_conversation_recent", "conversation_id", "sequence"),
    )


class ChatCitation(Base):
    __tablename__ = "chat_citations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    source: Mapped[str] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(2048))
    excerpt: Mapped[str | None] = mapped_column(String(500))


class MessageFeedback(Base):
    __tablename__ = "chat_message_feedback"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_chat_feedback_user"),)
