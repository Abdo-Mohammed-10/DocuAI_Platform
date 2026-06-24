import uuid
from contextvars import ContextVar

request_id_ctx = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    rid = str(uuid.uuid4())
    request_id_ctx.set(rid)
    return rid


def get_request_id() -> str | None:
    return request_id_ctx.get()
