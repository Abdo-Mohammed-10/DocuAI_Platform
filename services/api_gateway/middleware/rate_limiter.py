from __future__ import annotations

import time
import uuid
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status

from services.api_gateway.middleware.auth import get_current_user
from shared.config import settings
from shared.db.models.user import User

RATE_LIMIT = 60
WINDOW_SECS = 60

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis

    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            encoding="utf-8",
            max_connections=20,
        )

    return _redis


def get_client_identifier(
    request: Request,
    current_user: User | None = None,
) -> str:

    if current_user:
        return f"user:{current_user.id}"

    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

    return f"ip:{client_ip}"


async def rate_limit(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    redis = await get_redis()

    identifier = get_client_identifier(
        request=request,
        current_user=current_user,
    )

    key = f"rate_limit:{identifier}"

    now = time.time()
    window_start = now - WINDOW_SECS

    pipe = redis.pipeline(transaction=True)

    pipe.zremrangebyscore(
        key,
        0,
        window_start,
    )

    pipe.zadd(
        key,
        {
            f"{now}:{uuid.uuid4()}": now
        },
    )

    pipe.zcard(key)

    pipe.expire(
        key,
        WINDOW_SECS,
    )

    results = await pipe.execute()

    request_count = results[2]

    if request_count > RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": (
                    f"Max {RATE_LIMIT} requests "
                    f"per {WINDOW_SECS} seconds"
                ),
                "retry_after": WINDOW_SECS,
            },
            headers={
                "Retry-After": str(WINDOW_SECS),
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
            },
        )

    request.state.rate_limit = {
        "limit": RATE_LIMIT,
        "remaining": max(
            RATE_LIMIT - request_count,
            0,
        ),
        "identifier": identifier,
    }