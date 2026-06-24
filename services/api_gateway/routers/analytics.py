from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.middleware.auth import get_current_user
from shared.db.models.chat_session import ChatMessage
from shared.db.models.document import Document
from shared.db.models.user import User
from shared.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.owner_id == current_user.id
        )
    )

    msg_result = await db.execute(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.user_id == current_user.id
        )
    )

    return {
        "user_id": str(current_user.id),
        "total_documents": doc_result.scalar_one(),
        "total_messages": msg_result.scalar_one(),
    }