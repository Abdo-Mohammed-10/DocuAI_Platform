import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db.models.chunk import Chunk
from services.nlp_service.llm.client import get_llm
from services.nlp_service.llm.prompt_templates import CLASSIFY_PROMPT

VALID_CATEGORIES = {
    "invoice", "contract", "report",
    "research_paper", "legal", "other"
}


class DocumentClassifier:
    def __init__(self):
        self.llm = get_llm(temperature=0.0)

    async def classify(
        self,
        document_id: uuid.UUID,
        db: AsyncSession,
    ) -> str:
        result = await db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
            .limit(3)
        )
        chunks = result.scalars().all()
        text = " ".join(c.content for c in chunks)[:3000]

        chain = CLASSIFY_PROMPT | self.llm
        response = await chain.ainvoke({"text": text})
        category = response.content.strip().lower()

        return category if category in VALID_CATEGORIES else "other"