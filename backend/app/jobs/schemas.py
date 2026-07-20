import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    queue: str
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class JobHealth(BaseModel):
    queued: int
    running: int
    failed: int
    dead_lettered: int
    completed: int
    redis: str
    status: str
