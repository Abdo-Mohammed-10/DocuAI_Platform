import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
)
from services.ingestion_service.tasks.celery_tasks import process_document
from shared.db.models.document import Document, DocumentStatus
from shared.db.models.user import User
from shared.db.session import get_db
from services.ingestion_service.virus_scanner import VirusScanner
from prometheus_fastapi_instrumentator import Instrumentator

scanner = VirusScanner()

app = FastAPI(title="Ingestion Service", version="0.1.0")
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion"}


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()

    # ← scan
    is_safe, reason = scanner.scan(file_bytes, file.filename)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"File rejected: {reason}")

    # Validate
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if len(file_bytes) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    # ✅ استخدام الـ user_id الحقيقي القادم من الـ Gateway
    try:
        owner_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    result = await db.execute(select(User).where(User.id == owner_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # إنشاء document record
    doc = Document(
        owner_id=user.id,
        filename=file.filename,
        file_size=len(file_bytes),
        status=DocumentStatus.pending,
        s3_key=f"documents/{uuid.uuid4()}/{file.filename}",
    )

    db.add(doc)
    await db.flush()
    await db.commit()
    await db.refresh(doc)

    doc_id = str(doc.id)
    process_document.delay(doc_id, file_bytes.hex())

    return doc


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/documents", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()