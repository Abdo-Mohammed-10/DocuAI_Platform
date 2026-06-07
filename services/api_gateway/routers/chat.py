import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models.chat_session import ChatMessage, ChatSession
from shared.db.models.user import User
from shared.db.session import get_db
from shared.http_client import post_json
from shared.tracing import get_request_id
from shared.circuit_breaker import breaker

from services.api_gateway.middleware.auth import get_current_user
from services.api_gateway.middleware.rate_limiter import rate_limit


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(rate_limit)],
)

NLP_URL = "http://localhost:8002"


# ─────────────────────────────
# Schemas
# ─────────────────────────────
class AskRequest(BaseModel):
    document_id: uuid.UUID
    question: str


class MessageResponse(BaseModel):
    role: str
    content: str

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    title: str | None
    messages: list[MessageResponse]

    model_config = {"from_attributes": True}


# ─────────────────────────────
# Endpoints
# ─────────────────────────────
@router.post("/ask")
async def ask(
    req: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    1. ابعت السؤال للـ NLP service
    2. احفظ الـ conversation في DB
    3. ارجع الإجابة
    """

    # Call NLP service
    resp = await breaker.call_async(
        post_json,
        f"{NLP_URL}/ask",
        json={
            "document_id": str(req.document_id),
            "question": req.question,
        },
        headers={
            "X-Request-ID": get_request_id(),
        },
    )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail="NLP service error",
        )

    nlp_result = resp.json()

    # Get or create chat session
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.user_id == current_user.id,
            ChatSession.document_id == req.document_id,
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(
            user_id=current_user.id,
            document_id=req.document_id,
            title=req.question[:100],
        )

        db.add(session)
        await db.flush()

    # Save user message
    db.add(
        ChatMessage(
            session_id=session.id,
            role="user",
            content=req.question,
        )
    )

    # Save assistant message
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=nlp_result["answer"],
            meta={
                "source_chunks": nlp_result.get("source_chunks", []),
                "latency_ms": nlp_result.get("latency_ms", 0),
                "retries": nlp_result.get("retries", 0),
            },
        )
    )

    await db.commit()

    return {
        "answer": nlp_result["answer"],
        "source_chunks": nlp_result.get("source_chunks", []),
        "latency_ms": nlp_result.get("latency_ms", 0),
        "session_id": str(session.id),
    }


@router.get(
    "/history/{document_id}",
    response_model=SessionResponse,
)
async def get_history(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.user_id == current_user.id,
            ChatSession.document_id == document_id,
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="No chat history found",
        )

    return session