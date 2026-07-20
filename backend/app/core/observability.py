import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

REQUEST_COUNTERS: dict[str, int] = {"total": 0, "errors": 0}
REQUEST_LATENCY_MS: list[float] = []


async def request_observability_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    started = time.perf_counter()
    REQUEST_COUNTERS["total"] += 1
    try:
        response = await call_next(request)
    except Exception:
        REQUEST_COUNTERS["errors"] += 1
        structlog.get_logger().exception("request_failed")
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    REQUEST_LATENCY_MS.append(elapsed_ms)
    if len(REQUEST_LATENCY_MS) > 500:
        del REQUEST_LATENCY_MS[:250]
    response.headers["X-Request-ID"] = request_id
    response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.2f}"
    structlog.get_logger().info(
        "request_completed",
        method=request.method,
        status_code=response.status_code,
        elapsed_ms=round(elapsed_ms, 2),
    )
    return response


def metrics_snapshot() -> dict[str, float | int]:
    sample = REQUEST_LATENCY_MS[-100:]
    avg = sum(sample) / len(sample) if sample else 0
    return {
        "requests_total": REQUEST_COUNTERS["total"],
        "request_errors_total": REQUEST_COUNTERS["errors"],
        "request_latency_avg_ms": round(avg, 2),
    }
