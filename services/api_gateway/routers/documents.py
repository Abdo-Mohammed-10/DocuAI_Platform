import uuid

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.middleware.auth import get_current_user
from services.api_gateway.middleware.rate_limiter import rate_limit
from services.api_gateway.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
)
from shared.db.models.document import Document
from shared.db.models.user import User
from shared.db.session import get_db

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(rate_limit)],
)

INGESTION_URL = "http://localhost:8001"


# Upload document endpoint - forwards to ingestion service
@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{INGESTION_URL}/documents/upload",
            files={
                "file": (
                    file.filename,
                    file.file,
                    file.content_type,
                )
            },
            data={
                "user_id": str(current_user.id)
            },
        )

    if resp.status_code != 200:
        try:
            detail = resp.json().get(
                "detail",
                "Upload failed",
            )
        except Exception:
            detail = resp.text

        raise HTTPException(
            status_code=resp.status_code,
            detail=detail,
        )

    return resp.json()


# List documents
@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


# Get single document
@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )

    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc