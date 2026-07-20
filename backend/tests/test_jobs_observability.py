import uuid
from datetime import UTC, datetime

import pytest

from app.jobs.models import BackgroundJob
from app.jobs.service import mark_failed


class FakeRedis:
    def __init__(self) -> None:
        self.dead_letters: list[str] = []
        self.requeued: list[str] = []

    async def lpush(self, key: str, value: str) -> None:
        if key.endswith(":dead"):
            self.dead_letters.append(value)
        else:
            self.requeued.append(value)


class FakeDb:
    async def flush(self) -> None:
        return None


def job(attempts: int, max_attempts: int) -> BackgroundJob:
    now = datetime.now(UTC)
    return BackgroundJob(
        id=uuid.uuid4(),
        queue="reports",
        job_type="report_processing",
        status="running",
        idempotency_key=str(uuid.uuid4()),
        owner_user_id=uuid.uuid4(),
        payload_json={},
        attempts=attempts,
        max_attempts=max_attempts,
        scheduled_at=now,
        started_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_job_failure_requeues_before_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr("app.jobs.service.get_redis", lambda: redis)
    item = job(attempts=1, max_attempts=3)
    await mark_failed(FakeDb(), item, RuntimeError("temporary"))  # type: ignore[arg-type]
    assert item.status == "queued"
    assert redis.requeued == [str(item.id)]
    assert not redis.dead_letters


@pytest.mark.asyncio
async def test_job_failure_dead_letters_after_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr("app.jobs.service.get_redis", lambda: redis)
    item = job(attempts=3, max_attempts=3)
    await mark_failed(FakeDb(), item, RuntimeError("boom"))  # type: ignore[arg-type]
    assert item.status == "dead_lettered"
    assert redis.dead_letters
    assert not redis.requeued
