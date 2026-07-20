import inspect
import json
import uuid
from collections.abc import Awaitable
from datetime import UTC, datetime, timedelta
from typing import TypeVar, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.jobs.models import BackgroundJob, CacheInvalidationLog

QUEUE_KEY = "healthguard:jobs"
DEAD_LETTER_QUEUE = "healthguard:jobs:dead"
LOCK_PREFIX = "healthguard:lock:"
CACHE_PREFIX = "healthguard:cache:"
T = TypeVar("T")


async def _resolve(value: T | Awaitable[T]) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


async def enqueue_job(
    db: AsyncSession,
    *,
    job_type: str,
    payload: dict[str, object],
    queue: str = "default",
    owner_user_id: uuid.UUID | None = None,
    idempotency_key: str,
    max_attempts: int = 3,
) -> BackgroundJob:
    existing = await db.scalar(
        select(BackgroundJob).where(BackgroundJob.idempotency_key == idempotency_key)
    )
    if existing:
        return existing
    now = datetime.now(UTC)
    job = BackgroundJob(
        queue=queue,
        job_type=job_type,
        status="queued",
        idempotency_key=idempotency_key,
        owner_user_id=owner_user_id,
        payload_json=payload,
        attempts=0,
        max_attempts=max_attempts,
        scheduled_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.flush()
    await _resolve(get_redis().lpush(QUEUE_KEY, str(job.id)))
    return job


async def acquire_lock(name: str, *, ttl_seconds: int = 60) -> bool:
    return bool(
        await _resolve(get_redis().set(f"{LOCK_PREFIX}{name}", "1", ex=ttl_seconds, nx=True))
    )


async def release_lock(name: str) -> None:
    await _resolve(get_redis().delete(f"{LOCK_PREFIX}{name}"))


async def mark_started(job: BackgroundJob) -> None:
    job.status = "running"
    job.attempts += 1
    job.started_at = datetime.now(UTC)
    job.locked_until = datetime.now(UTC) + timedelta(minutes=5)
    job.updated_at = datetime.now(UTC)


async def mark_completed(job: BackgroundJob) -> None:
    job.status = "completed"
    job.completed_at = datetime.now(UTC)
    job.locked_until = None
    job.updated_at = datetime.now(UTC)


async def mark_failed(db: AsyncSession, job: BackgroundJob, error: Exception) -> None:
    job.last_error = str(error)[:1000]
    job.updated_at = datetime.now(UTC)
    job.locked_until = None
    if job.attempts >= job.max_attempts:
        job.status = "dead_lettered"
        await _resolve(
            get_redis().lpush(
                DEAD_LETTER_QUEUE, json.dumps({"job_id": str(job.id), "error": job.last_error})
            )
        )
    else:
        job.status = "queued"
        job.scheduled_at = datetime.now(UTC) + timedelta(seconds=min(300, 2**job.attempts * 15))
        await _resolve(get_redis().lpush(QUEUE_KEY, str(job.id)))
    await db.flush()


async def cache_get_json(key: str) -> object | None:
    value = await _resolve(get_redis().get(f"{CACHE_PREFIX}{key}"))
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return cast(object, json.loads(value))


async def cache_set_json(key: str, value: object, *, ttl_seconds: int = 300) -> None:
    await _resolve(
        get_redis().set(f"{CACHE_PREFIX}{key}", json.dumps(value, default=str), ex=ttl_seconds)
    )


async def invalidate_cache(db: AsyncSession, key: str, reason: str) -> None:
    await _resolve(get_redis().delete(f"{CACHE_PREFIX}{key}"))
    db.add(CacheInvalidationLog(cache_key=key, reason=reason, created_at=datetime.now(UTC)))


async def job_counts(db: AsyncSession) -> dict[str, int]:
    result: dict[str, int] = {
        "queued": 0,
        "running": 0,
        "failed": 0,
        "dead_lettered": 0,
        "completed": 0,
    }
    rows = await db.execute(
        select(BackgroundJob.status, func.count()).group_by(BackgroundJob.status)
    )
    for status, count in rows.tuples():
        if status in result:
            result[status] = count
    return result
