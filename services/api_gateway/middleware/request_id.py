from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from shared.tracing import generate_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get(
            "X-Request-ID"
        ) or generate_request_id()

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response