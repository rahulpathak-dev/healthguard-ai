import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MedicineSearchHistory(Base):
    __tablename__ = "medicine_search_history"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    query: Mapped[str] = mapped_column(String(160))
    normalized_query: Mapped[str] = mapped_column(String(160), index=True)
    matched_generic_name: Mapped[str | None] = mapped_column(String(160))
    source_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_medicine_search_history_user_recent", "user_id", "created_at"),)
