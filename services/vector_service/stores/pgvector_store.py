import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from services.vector_service.embeddings.encoder import TextEncoder
from shared.db.models.chunk import Chunk


class PGVectorStore:
    def __init__(self):
        self.encoder = TextEncoder()

    async def save_embeddings(self, document_id: uuid.UUID, db: AsyncSession) -> int:
        result = await db.execute(
            select(Chunk).where(
                Chunk.document_id == document_id,
                Chunk.embedding.is_(None),
            )
        )
        chunks = result.scalars().all()
        if not chunks:
            return 0

        texts = [c.content for c in chunks]
        embeddings = self.encoder.encode_batch(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        await db.flush()
        return len(chunks)

    async def similarity_search(
        self,
        query: str,
        document_id: uuid.UUID,
        db: AsyncSession,
        top_k: int = 5,
    ) -> list[dict]:
        query_embedding = self.encoder.encode(query)
        # نحط الـ vector مباشرة في الـ SQL عشان asyncpg مش بيدعم named params مع ::vector
        query_vec_str = str(query_embedding)

        stmt = text(f"""
            SELECT
                id,
                content,
                chunk_index,
                page_number,
                token_count,
                1 - (embedding <=> '{query_vec_str}'::vector) AS similarity
            FROM chunks
            WHERE document_id = :doc_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> '{query_vec_str}'::vector
            LIMIT :top_k
        """)

        result = await db.execute(
            stmt,
            {
                "doc_id": str(document_id),
                "top_k": top_k,
            },
        )

        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "content": row.content,
                "chunk_index": row.chunk_index,
                "page_number": row.page_number,
                "token_count": row.token_count,
                "similarity": round(float(row.similarity), 4),
                "preview": row.content[:200],
            }
            for row in rows
        ]

    async def create_index(self, db: AsyncSession):
        await db.execute(
            text("""
                CREATE INDEX IF NOT EXISTS chunks_embedding_idx
                ON chunks
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
        )
        await db.commit()