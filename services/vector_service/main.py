import uuid
import time

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.vector_service.stores.pgvector_store import PGVectorStore
from shared.db.session import get_db
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Vector Service", version="0.1.0")
Instrumentator().instrument(app).expose(app)

store = PGVectorStore()


# ---- Schemas ----
class SearchRequest(BaseModel):
    document_id: uuid.UUID
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    id: str
    content: str
    chunk_index: int
    page_number: int
    token_count: int
    similarity: float
    preview: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class EmbedRequest(BaseModel):
    document_id: uuid.UUID


# ---- Endpoints ----
@app.get("/health")
async def health():
    return {"status": "ok", "service": "vector"}


@app.post("/embed")
async def embed_document(
    req: EmbedRequest,
    db: AsyncSession = Depends(get_db),
):
    count = await store.save_embeddings(req.document_id, db)
    await db.commit()
    return {"document_id": req.document_id, "embedded_chunks": count}


@app.post("/search", response_model=SearchResponse)
async def semantic_search(
    req: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    start = time.time()

    results = await store.similarity_search(
        query=req.query,
        document_id=req.document_id,
        db=db,
        top_k=req.top_k,
    )

    latency = round(time.time() - start, 3)

    if not results:
        raise HTTPException(status_code=404, detail="No chunks found for this document")

    return SearchResponse(
        query=req.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@app.post("/index")
async def create_index(db: AsyncSession = Depends(get_db)):
    await store.create_index(db)
    return {"status": "index created"}