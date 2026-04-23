"""
Rate limiting engine.

Strategy: Fixed window
- Count requests per client within the current window.
- If count >= limit, reject with 429.
- Window boundaries are derived from the current timestamp floored to window size.

Extension point: swap _count_requests_in_window() with sliding window or token bucket.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app import db
from app.models import Client, RateLimitConfig, RequestLog


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int | None = None  # seconds until window resets (only when blocked)


DEFAULT_REQUESTS_PER_WINDOW = 60
DEFAULT_WINDOW_SECONDS = 60


def check_and_record(client: Client, path: str) -> RateLimitResult:
    """
    Check the rate limit for a client, record the request, and return the result.
    This is the single entry point for all rate-limit decisions.
    """
    config = _get_config(client)
    window_start = _current_window_start(config.window_seconds)
    count = _count_requests_in_window(client.id, window_start)

    allowed = count < config.requests_per_window
    remaining = max(0, config.requests_per_window - count - (1 if allowed else 0))

    status_code = 200 if allowed else 429
    _record_request(client.id, path, status_code, was_throttled=not allowed)

    retry_after = None
    if not allowed:
        window_end = window_start + timedelta(seconds=config.window_seconds)
        retry_after = max(1, int((window_end - datetime.now(timezone.utc)).total_seconds()))

    return RateLimitResult(
        allowed=allowed,
        limit=config.requests_per_window,
        remaining=remaining,
        retry_after=retry_after,
    )


def _get_config(client: Client) -> RateLimitConfig:
    if client.rate_config:
        return client.rate_config

    # Fallback defaults; should not happen after proper client creation.
    return RateLimitConfig(
        client_id=client.id,
        requests_per_window=DEFAULT_REQUESTS_PER_WINDOW,
        window_seconds=DEFAULT_WINDOW_SECONDS,
    )


def _current_window_start(window_seconds: int) -> datetime:
    now = datetime.now(timezone.utc)
    floored = (int(now.timestamp()) // window_seconds) * window_seconds
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def _count_requests_in_window(client_id: int, window_start: datetime) -> int:
    return (
        db.session.query(RequestLog)
        .filter(
            RequestLog.client_id == client_id,
            RequestLog.timestamp >= window_start,
        )
        .count()
    )


def _record_request(client_id: int, path: str, status_code: int, was_throttled: bool) -> None:
    log = RequestLog(
        client_id=client_id,
        path=path,
        status_code=status_code,
        was_throttled=was_throttled,
    )
    db.session.add(log)
    db.session.commit()
