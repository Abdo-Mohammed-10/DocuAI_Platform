from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.db.session import get_db
from shared.db.models.user import User
from shared.db.models.document import Document
from shared.db.models.chat_session import ChatMessage
from services.api_gateway.middleware.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    db:           AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # عدد الـ documents
    doc_count = await db.execute(
        select(func.count()).where(Document.owner_id == current_user.id)
    )

    # عدد الـ messages
    msg_count = await db.execute(
        select(func.count(ChatMessage.id))
    )

    return {
        "user_id":        str(current_user.id),
        "total_documents": doc_count.scalar(),
        "total_messages":  msg_count.scalar(),
    }