import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    computed_field,
    field_validator,
    model_validator,
)

from app.profiles.models import PermissionLevel, ProfileKind


class EmergencyContactInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    relationship: str | None = Field(default=None, max_length=80)
    phone: str = Field(min_length=7, max_length=32, pattern=r"^[0-9+() .-]+$")
    is_primary: bool = False


class AllergyInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    substance: str = Field(min_length=1, max_length=160)
    reaction_summary: str | None = Field(default=None, max_length=500)
    severity: Literal["mild", "moderate", "severe"] | None = None


class MedicineInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    dosage: str | None = Field(default=None, max_length=120)
    schedule: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, max_length=300)


class ConditionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=1000)
    diagnosed_on: date | None = None

    @field_validator("diagnosed_on")
    @classmethod
    def diagnosis_not_future(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("Diagnosis date cannot be in the future")
        return value


class ProfileFields(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    relationship: str | None = Field(default=None, max_length=80)
    date_of_birth: date | None = None
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None
    sex_at_birth: str | None = Field(default=None, max_length=40)
    gender_identity: str | None = Field(default=None, max_length=80)
    pronouns: str | None = Field(default=None, max_length=40)
    avatar_url: HttpUrl | None = None
    locale: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=4000)
    allow_doctor_access: bool | None = None
    share_with_family: bool | None = None
    emergency_contacts: list[EmergencyContactInput] | None = Field(default=None, max_length=10)
    allergies: list[AllergyInput] | None = Field(default=None, max_length=50)
    medicines: list[MedicineInput] | None = Field(default=None, max_length=100)
    chronic_conditions: list[ConditionInput] | None = Field(default=None, max_length=50)

    @field_validator("date_of_birth")
    @classmethod
    def valid_birth_date(cls, value: date | None) -> date | None:
        if value is None:
            return value
        today = date.today()
        if value > today:
            raise ValueError("Date of birth cannot be in the future")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age > 130:
            raise ValueError("Date of birth is outside the supported range")
        return value

    @field_validator("avatar_url")
    @classmethod
    def secure_avatar(cls, value: HttpUrl | None) -> HttpUrl | None:
        if value and value.scheme != "https":
            raise ValueError("Avatar URL must use HTTPS")
        return value

    @model_validator(mode="after")
    def one_primary_contact(self) -> "ProfileFields":
        if self.emergency_contacts and sum(item.is_primary for item in self.emergency_contacts) > 1:
            raise ValueError("Only one emergency contact can be primary")
        return self


class ProfileCreate(ProfileFields):
    kind: ProfileKind
    display_name: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def relationship_for_family(self) -> "ProfileCreate":
        if self.kind == ProfileKind.FAMILY and not self.relationship:
            raise ValueError("Relationship is required for a family profile")
        if self.kind == ProfileKind.PERSONAL and self.relationship:
            raise ValueError("A personal profile cannot have a family relationship")
        return self


class ProfileUpdate(ProfileFields):
    @model_validator(mode="after")
    def required_identity_fields(self) -> "ProfileUpdate":
        if "display_name" in self.model_fields_set and self.display_name is None:
            raise ValueError("Display name cannot be empty")
        return self


class EmergencyContactView(EmergencyContactInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class AllergyView(AllergyInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class MedicineView(MedicineInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ConditionView(ConditionInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ProfileView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    kind: ProfileKind
    display_name: str
    relationship: str | None
    date_of_birth: date | None
    blood_group: str | None
    sex_at_birth: str | None
    gender_identity: str | None
    pronouns: str | None
    avatar_url: str | None
    locale: str | None
    timezone: str | None
    notes: str | None
    allow_doctor_access: bool
    share_with_family: bool
    created_at: datetime
    updated_at: datetime
    emergency_contacts: list[EmergencyContactView]
    allergies: list[AllergyView]
    medicines: list[MedicineView]
    chronic_conditions: list[ConditionView]
    can_edit: bool = False
    is_owner: bool = False

    @property
    @computed_field
    def age(self) -> int | None:
        if self.date_of_birth is None:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )


class PermissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grantee_user_id: uuid.UUID
    level: PermissionLevel


class PermissionView(PermissionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
