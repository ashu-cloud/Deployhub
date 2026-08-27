"""Fixed-window rate limiting backed by Redis.

The API gateway is expected to enforce coarse-grained limits, but the
service itself must not be unbounded -- a client that bypasses the gateway
(or a gateway misconfiguration) should still be throttled here.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.redis import redis_client
from app.core.security import get_current_user


async def enforce_rate_limit(key: str, *, max_requests: int, window_seconds: int) -> None:
    redis_key = f"ratelimit:{key}"
    current = await redis_client.incr(redis_key)
    if current == 1:
        await redis_client.expire(redis_key, window_seconds)
    if current > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, slow down",
        )


async def rate_limit_create_project(user_id: str = Depends(get_current_user)) -> str:
    from app.core.config import settings

    await enforce_rate_limit(
        f"create-project:{user_id}",
        max_requests=settings.RATE_LIMIT_CREATE_PROJECT_MAX,
        window_seconds=settings.RATE_LIMIT_CREATE_PROJECT_WINDOW_SECONDS,
    )
    return user_id
