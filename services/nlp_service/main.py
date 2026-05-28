import uuid

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.mlflow_tracker import LLMTracker
from services.nlp_service.pipelines.classifier import DocumentClassifier
from services.nlp_service.pipelines.rag_pipeline import RAGPipeline
from services.nlp_service.pipelines.summarizer import Summarizer
from shared.db.models.document import Document, DocumentStatus
from shared.db.session import get_db

app = FastAPI(title="NLP Service", version="0.1.0")

rag = RAGPipeline(top_k=5)
summarizer = Summarizer()
classifier = DocumentClassifier()
tracker = LLMTracker()


class QuestionRequest(BaseModel):
    document_id: uuid.UUID
    question: str


class QuestionResponse(BaseModel):
    answer: str
    source_chunks: list[dict]
    latency_ms: float
    input_tokens: int
    output_tokens: int


class SummaryRequest(BaseModel):
    document_id: uuid.UUID
    language: str = "English"


async def get_ready_document(
    document_id: uuid.UUID,
    db: AsyncSession,
) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.DONE:
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready yet. Status: {doc.status}",
        )
    return doc


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nlp"}


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    req: QuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_ready_document(req.document_id, db)

    result = await rag.run(
        question=req.question,
        document_id=req.document_id,
        db=db,
    )

    # MLflow
    tracker.log_rag_call(
        question=req.question,
        result=result,
        document_id=str(req.document_id),
    )

    return QuestionResponse(
        answer=result.answer,
        source_chunks=result.source_chunks,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )


@app.post("/summarize")
async def summarize(
    req: SummaryRequest,
    db: AsyncSession = Depends(get_db),
):
    await get_ready_document(req.document_id, db)
    summary = await summarizer.summarize(req.document_id, db, req.language)
    return {"document_id": req.document_id, "summary": summary}


@app.post("/classify")
async def classify(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await get_ready_document(document_id, db)
    category = await classifier.classify(document_id, db)
    return {"document_id": document_id, "category": category}
