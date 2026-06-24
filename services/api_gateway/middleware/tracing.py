import uuid
from fastapi import Request, Response
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("api_gateway.tracing")


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()

        request_id = getattr(request.state, "request_id", "unknown")

        response = await call_next(request)

        latency_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method":     request.method,
                "path":       request.url.path,
                "status":     response.status_code,
                "latency_ms": latency_ms,
            },
        )

        response.headers["X-Latency-Ms"] = str(latency_ms)
        return response