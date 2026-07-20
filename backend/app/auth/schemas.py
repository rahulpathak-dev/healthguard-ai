import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.auth.models import UserRole


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not any(c.islower() for c in value) or not any(c.isupper() for c in value):
            raise ValueError("Password must contain upper and lowercase characters")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain a number")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class ResetPasswordRequest(TokenRequest):
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return RegisterRequest.strong_password(value)


class RoleUpdateRequest(BaseModel):
    role: UserRole


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    is_email_verified: bool
    created_at: datetime


class SessionView(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    is_current: bool


class MessageView(BaseModel):
    message: str
