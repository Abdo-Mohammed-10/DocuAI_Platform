import uuid

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.schemas.document import (
    DocumentResponse,
    DocumentsUploadedResponse,
)
from services.ingestion_service.tasks.celery_tasks import process_document
from shared.db.models.document import Document, DocumentStatus
from shared.db.models.user import User
from shared.db.session import get_db

app = FastAPI(title="Ingestion Service", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "DocuAI API running"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion"}


@app.post("/documents/upload", response_model=DocumentsUploadedResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        # create demo user
        user = User(
            email="abdo@gmail.com",
            hashed_password="abdo123",
            full_name="abdo mohamed",
        )
        db.add(user)
        await db.flush()

    # document record
    doc = Document(
        owner_id=user.id,
        filename=file.filename,
        file_size=len(file_bytes),
        status=DocumentStatus.PENDING,
        s3_key=f"documents/{uuid.uuid4()}/{file.filename}",
    )
    db.add(doc)
    await db.flush()
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
