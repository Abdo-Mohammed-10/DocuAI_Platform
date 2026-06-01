import uuid
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db.session import get_db
from shared.db.models.document import Document, DocumentStatus
from services.vector_service.stores.pgvector_store import PGVectorStore

app = FastAPI(title="Vector Service", version="0.1.0")
store = PGVectorStore()


#  Schemas 
class SearchRequest(BaseModel):
    document_id: uuid.UUID
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    id: str
    content: str
    chunk_index: int
    page_number: int | None
    similarity: float
    preview: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


#  Endpoints 
@app.get("/health")
async def health():
    return {"status": "ok", "service": "vector"}


@app.post("/embed/{document_id}")
async def embed_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.DONE:
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready. Status: {doc.status}",
        )

    count = await store.save_embeddings(document_id, db)
    await db.commit()

    return {
        "document_id": document_id,
        "chunks_embedded": count,
        "message": f"Successfully embedded {count} chunks",
    }


@app.post("/search", response_model=SearchResponse)
async def semantic_search(
    req: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    results = await store.similarity_search(
        query=req.query,
        document_id=req.document_id,
        db=db,
        top_k=req.top_k,
    )

    return SearchResponse(
        query=req.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@app.post("/index/create")
async def create_hnsw_index(db: AsyncSession = Depends(get_db)):

    await store.create_index(db)
    return {"message": "HNSW index created successfully"}
