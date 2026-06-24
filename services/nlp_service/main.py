import time
import uuid

from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.mlflow_tracker import LLMTracker
from services.analytics_service.metrics.prometheus_metrics import (
    llm_latency_seconds,
    llm_requests_total,
    rag_retries_total,
)
from services.nlp_service.pipelines.agentic_rag import rag_graph
from services.nlp_service.pipelines.classifier import DocumentClassifier
from services.nlp_service.pipelines.summarizer import Summarizer
from shared.db.models.document import Document, DocumentStatus
from shared.db.session import get_db
from shared.langsmith_setup import init_langsmith

init_langsmith()

app = FastAPI(title="NLP Service", version="0.1.0")

# ── Prometheus default metrics (request count, latency, etc) ──
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

summarizer  = Summarizer()
classifier  = DocumentClassifier()
tracker     = LLMTracker()

# ── Schemas ────────────────────────────────────────────────────────────────
class QuestionRequest(BaseModel):
    document_id: uuid.UUID
    question: str


class QuestionResponse(BaseModel):
    answer: str
    source_chunks: list[dict]
    latency_ms: float
    retries: int


class SummaryRequest(BaseModel):
    document_id: uuid.UUID
    language: str = "English"


# ── Helpers ────────────────────────────────────────────────────────────────
async def get_ready_document(doc_id: uuid.UUID, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.done:
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready. Status: {doc.status}",
        )
    return doc

# ── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "nlp"}


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    req: QuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_ready_document(req.document_id, db)

    start = time.time()
    status_label = "success"

    try:
        final_state = await rag_graph.ainvoke({
            "question":    req.question,
            "document_id": str(req.document_id),
            "chunks":      [],
            "context":     "",
            "answer":      "",
            "is_relevant": False,
            "retry_count": 0,
            "db":          db,
        })
    except Exception:
        status_label = "error"
        llm_requests_total.labels(
            service="nlp", endpoint="/ask", status=status_label
        ).inc()
        raise

    latency = time.time() - start

    # ── Record Prometheus metrics ─────────────────────────
    llm_requests_total.labels(
        service="nlp", endpoint="/ask", status=status_label
    ).inc()

    llm_latency_seconds.labels(
        service="nlp", endpoint="/ask"
    ).observe(latency)

    retries = final_state.get("retry_count", 0)
    if retries:
        rag_retries_total.inc(retries)

    # ── MLflow tracking (existing) ────────────────────────
    class _Result:
        pass
    result = _Result()
    result.source_chunks = final_state["chunks"]
    result.latency_ms = round(latency * 1000, 2)
    result.input_tokens = 0
    result.output_tokens = 0

    tracker.log_rag_call(
        question=req.question,
        result=result,
        document_id=str(req.document_id),
    )

    return QuestionResponse(
        answer=final_state["answer"],
        source_chunks=final_state["chunks"],
        latency_ms=round(latency * 1000, 2),
        retries=retries,
    )


@app.post("/summarize")
async def summarize(
    req: SummaryRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_ready_document(req.document_id, db)

    start = time.time()
    summary = await summarizer.summarize(req.document_id, db, req.language)
    latency = time.time() - start

    llm_requests_total.labels(
        service="nlp", endpoint="/summarize", status="success"
    ).inc()
    llm_latency_seconds.labels(
        service="nlp", endpoint="/summarize"
    ).observe(latency)

    return {"document_id": req.document_id, "summary": summary}


@app.post("/classify")
async def classify(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_ready_document(document_id, db)

    start = time.time()
    category = await classifier.classify(document_id, db)
    latency = time.time() - start

    llm_requests_total.labels(
        service="nlp", endpoint="/classify", status="success"
    ).inc()
    llm_latency_seconds.labels(
        service="nlp", endpoint="/classify"
    ).observe(latency)

    return {"document_id": document_id, "category": category}