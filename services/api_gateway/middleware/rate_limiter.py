from __future__ import annotations

import time
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status

from shared.config import settings
from services.api_gateway.middleware.auth import get_current_user
from shared.db.models.user import User

# ── Config 
RATE_LIMIT = 60
WINDOW_SECS = 60

# ── Redis Singleton 
_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Reuse one Redis connection pool
    بدل ما نفتح connection جديد كل request
    """
    global _redis

    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            encoding="utf-8",
            max_connections=20,
        )

    return _redis


# ── Helpers 
def get_client_identifier(
    request: Request,
    current_user: User | None = None,
) -> str:
    """
    الأولوية للـ authenticated user
    fallback = client IP
    """

    # authenticated user
    if current_user:
        return f"user:{current_user.id}"

    # reverse proxy support
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host

    return f"ip:{client_ip}"


# ── Main Dependency 
async def rate_limit(
    request: Request,
    current_user: User | None = Depends(get_current_user),
):
    """
    Sliding Window Rate Limiter

    - Redis Sorted Set
    - Per-user limiting
    - Proxy-aware
    - Reused Redis pool
    """

    redis = await get_redis()

    identifier = get_client_identifier(
        request=request,
        current_user=current_user,
    )

    key = f"rate_limit:{identifier}"

    now = time.time()
    window_start = now - WINDOW_SECS

    pipe = redis.pipeline(transaction=True)

    # remove expired requests
    pipe.zremrangebyscore(key, 0, window_start)

    # add current request
    pipe.zadd(key, {str(now): now})

    # count active requests
    pipe.zcard(key)

    # auto cleanup
    pipe.expire(key, WINDOW_SECS)

    results = await pipe.execute()

    request_count = results[2]

    if request_count > RATE_LIMIT:
        retry_after = WINDOW_SECS

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": (
                    f"Max {RATE_LIMIT} requests "
                    f"per {WINDOW_SECS} seconds"
                ),
                "retry_after": retry_after,
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
            },
        )

    remaining = max(RATE_LIMIT - request_count, 0)

    # useful for logging/debugging
    request.state.rate_limit = {
        "limit": RATE_LIMIT,
        "remaining": remaining,
        "identifier": identifier,
    }