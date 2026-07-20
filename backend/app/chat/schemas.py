import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LANGUAGE_PATTERN = r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$"


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    profile_id: uuid.UUID
    title: str = Field(default="New health conversation", min_length=1, max_length=180)
    language: str = Field(default="en", max_length=16, pattern=LANGUAGE_PATTERN)


class ConversationRename(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=180)


class ConversationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    profile_id: uuid.UUID
    title: str
    language: str
    created_at: datetime
    last_message_at: datetime


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=4000)
    language: str | None = Field(default=None, max_length=16, pattern=LANGUAGE_PATTERN)

    @field_validator("content")
    @classmethod
    def storage_safe_content(cls, value: str) -> str:
        cleaned = "".join(
            character for character in value if character in "\n\t" or ord(character) >= 32
        ).strip()
        if not cleaned:
            raise ValueError("Message must contain visible text")
        return cleaned


class CitationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    source: str
    url: str
    excerpt: str | None


class MessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    language: str
    status: str
    sequence: int
    parent_message_id: uuid.UUID | None
    created_at: datetime
    citations: list[CitationView]


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    rating: Literal["helpful", "not_helpful"]
    reason: str | None = Field(default=None, max_length=500)


class SuggestedQuestion(BaseModel):
    id: str
    text: str


class ChatProfileOption(BaseModel):
    id: uuid.UUID
    display_name: str
    kind: str


class ChatBootstrap(BaseModel):
    profiles: list[ChatProfileOption]
    suggested_questions: list[SuggestedQuestion]
    disclaimer: str
    supported_languages: list[str]
