from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MedicineSearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    q: str = Field(min_length=2, max_length=120)

    @field_validator("q")
    @classmethod
    def visible_query(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Search query is required")
        return cleaned


class MedicineReference(BaseModel):
    title: str
    source: str
    url: str
    excerpt: str


class MedicineInformation(BaseModel):
    query: str
    generic_name: str | None
    brand_names: list[str]
    common_uses: list[str]
    common_side_effects: list[str]
    serious_warnings: list[str]
    precautions: list[str]
    interactions: list[str]
    storage_information: list[str]
    pregnancy_child_elderly_cautions: list[str]
    spelling_suggestions: list[str]
    source_references: list[MedicineReference]
    disclaimer: str
    unsupported_notice: str | None = None


class MedicineHistoryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    query: str
    matched_generic_name: str | None
    source_count: int
    created_at: datetime
