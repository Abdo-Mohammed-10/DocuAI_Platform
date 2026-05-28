import uuid
import time
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db.models.chunk import Chunk
from services.nlp_service.llm.client import get_llm
from services.nlp_service.llm.prompt_templates import RAG_PROMPT


@dataclass
class RAGResult:
    answer: str
    source_chunks: list[dict]
    latency_ms: float
    input_tokens: int
    output_tokens: int


class RAGPipeline:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.llm = get_llm()

    async def run(
        self,
        question: str,
        document_id: uuid.UUID,
        db: AsyncSession,
    ) -> RAGResult:
        start = time.time()

        chunks = await self._fetch_chunks(document_id, db)
        if not chunks:
            return RAGResult(
                answer="No content found for this document.",
                source_chunks=[],
                latency_ms=0,
                input_tokens=0,
                output_tokens=0,
            )

        relevant = self._select_relevant(question, chunks)

        context = "\n\n---\n\n".join([
            f"[Page {c.page_number}]: {c.content}"
            for c in relevant
        ])

        chain = RAG_PROMPT | self.llm
        response = await chain.ainvoke({
            "context": context,
            "question": question,
        })

        latency = (time.time() - start) * 1000

        usage = response.response_metadata.get("token_usage", {})

        return RAGResult(
            answer=response.content,
            source_chunks=[
                {
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number,
                    "preview": c.content[:200],
                }
                for c in relevant
            ],
            latency_ms=round(latency, 2),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )

    async def _fetch_chunks(
        self,
        document_id: uuid.UUID,
        db: AsyncSession,
    ) -> list[Chunk]:
        result = await db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        return result.scalars().all()

    def _select_relevant(
        self,
        question: str,
        chunks: list[Chunk],
    ) -> list[Chunk]:
        
        q_words = set(question.lower().split())

        def score(chunk: Chunk) -> int:
            words = set(chunk.content.lower().split())
            return len(q_words & words)

        ranked = sorted(chunks, key=score, reverse=True)
        return ranked[:self.top_k]