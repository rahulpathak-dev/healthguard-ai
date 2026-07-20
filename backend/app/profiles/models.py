import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship as orm_relationship

from app.db.base import Base


class ProfileKind(enum.StrEnum):
    PERSONAL = "personal"
    FAMILY = "family"


class PermissionLevel(enum.StrEnum):
    VIEW = "view"
    EDIT = "edit"


class HealthProfile(Base):
    __tablename__ = "health_profiles"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[ProfileKind] = mapped_column(Enum(ProfileKind), index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(120))
    relationship: Mapped[str | None] = mapped_column(String(80))
    dedupe_key: Mapped[str] = mapped_column(String(64))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    blood_group: Mapped[str | None] = mapped_column(String(3))
    sex_at_birth: Mapped[str | None] = mapped_column(String(40))
    gender_identity: Mapped[str | None] = mapped_column(String(80))
    pronouns: Mapped[str | None] = mapped_column(String(40))
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    locale: Mapped[str | None] = mapped_column(String(20))
    timezone: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)
    allow_doctor_access: Mapped[bool] = mapped_column(Boolean, default=False)
    share_with_family: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    emergency_contacts: Mapped[list["EmergencyContact"]] = orm_relationship(
        cascade="all, delete-orphan"
    )
    allergies: Mapped[list["Allergy"]] = orm_relationship(cascade="all, delete-orphan")
    medicines: Mapped[list["CurrentMedicine"]] = orm_relationship(cascade="all, delete-orphan")
    chronic_conditions: Mapped[list["ChronicCondition"]] = orm_relationship(
        cascade="all, delete-orphan"
    )
    __table_args__ = (
        UniqueConstraint("owner_user_id", "dedupe_key", name="uq_profile_owner_dedupe"),
        Index(
            "uq_personal_profile_owner",
            "owner_user_id",
            unique=True,
            postgresql_where=(kind == ProfileKind.PERSONAL),
            sqlite_where=(kind == ProfileKind.PERSONAL),
        ),
    )


class EmergencyContact(Base):
    __tablename__ = "profile_emergency_contacts"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    relationship: Mapped[str | None] = mapped_column(String(80))
    phone: Mapped[str] = mapped_column(String(32))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class Allergy(Base):
    __tablename__ = "profile_allergies"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    substance: Mapped[str] = mapped_column(String(160))
    reaction_summary: Mapped[str | None] = mapped_column(String(500))
    severity: Mapped[str | None] = mapped_column(String(20))


class CurrentMedicine(Base):
    __tablename__ = "profile_current_medicines"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    dosage: Mapped[str | None] = mapped_column(String(120))
    schedule: Mapped[str | None] = mapped_column(String(160))
    reason: Mapped[str | None] = mapped_column(String(300))


class ChronicCondition(Base):
    __tablename__ = "profile_chronic_conditions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(String(1000))
    diagnosed_on: Mapped[date | None] = mapped_column(Date)


class ProfilePermission(Base):
    __tablename__ = "profile_permissions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_profiles.id", ondelete="CASCADE"), index=True
    )
    grantee_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[PermissionLevel] = mapped_column(Enum(PermissionLevel))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("profile_id", "grantee_user_id", name="uq_profile_grantee"),)
