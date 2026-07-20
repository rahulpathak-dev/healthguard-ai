import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SymptomAssessment(Base):
    __tablename__ = "symptom_assessments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    symptoms_json: Mapped[list[str]] = mapped_column(JSON)
    duration: Mapped[str] = mapped_column(String(120))
    severity: Mapped[int] = mapped_column(Integer)
    age_group: Mapped[str] = mapped_column(String(40))
    relevant_context: Mapped[str | None] = mapped_column(Text)
    associated_symptoms_json: Mapped[list[str]] = mapped_column(JSON)
    warning_signs_json: Mapped[list[str]] = mapped_column(JSON)
    urgency_level: Mapped[str] = mapped_column(String(40), index=True)
    red_flags_json: Mapped[list[str]] = mapped_column(JSON)
    guidance_json: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_symptom_assessments_profile_created", "profile_id", "created_at"),)
