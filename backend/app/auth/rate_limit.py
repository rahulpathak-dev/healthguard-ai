from fastapi import HTTPException, Request, status

from app.db.redis import get_redis


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(scope: str, identity: str, limit: int, window_seconds: int) -> None:
    key = f"rate:{scope}:{identity}"
    redis = get_redis()
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(window_seconds)},
        )
