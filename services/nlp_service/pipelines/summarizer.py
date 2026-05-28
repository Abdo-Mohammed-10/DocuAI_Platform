import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db.models.chunk import Chunk
from services.nlp_service.llm.client import get_llm
from services.nlp_service.llm.prompt_templates import SUMMARIZE_PROMPT


class Summarizer:
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.max_chars = 12000 

    async def summarize(
        self,
        document_id: uuid.UUID,
        db: AsyncSession,
        language: str = "English",
    ) -> str:
        result = await db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        chunks = result.scalars().all()

        full_text = " ".join(c.content for c in chunks)
        truncated = full_text[:self.max_chars]

        chain = SUMMARIZE_PROMPT | self.llm
        response = await chain.ainvoke({
            "text": truncated,
            "language": language,
        })
        return response.content