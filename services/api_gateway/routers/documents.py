import uuid
from typing import Annotated

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models.document import Document
from shared.db.models.user import User
from shared.db.session import get_db

from services.api_gateway.middleware.auth import get_current_user
from services.api_gateway.middleware.rate_limiter import rate_limit
from services.api_gateway.schemas.document import (
    DocumentResponse,
    DocumentsUploadedResponse,
)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(rate_limit)],
)

INGESTION_URL = "http://localhost:8001"

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 20
ALLOWED_TYPES = {
    "application/pdf",
}


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
async def validate_upload(file: UploadFile) -> bytes:
    """
    Validate uploaded file:
    - content type
    - size
    """

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are allowed",
        )

    content = await file.read()

    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Max file size is {MAX_FILE_SIZE_MB} MB",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    return content


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────
@router.post(
    "/upload",
    response_model=DocumentsUploadedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload document through ingestion service.
    """

    file_bytes = await validate_upload(file)

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
        ) as client:

            response = await client.post(
                f"{INGESTION_URL}/documents/upload",
                files={
                    "file": (
                        file.filename,
                        file_bytes,
                        file.content_type,
                    )
                },
                data={
                    "user_id": str(current_user.id),
                },
            )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion service unavailable",
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ingestion service timeout",
        )

    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed communicating with ingestion service",
        )

    if response.status_code >= 400:
        try:
            error_detail = response.json().get("detail")
        except Exception:
            error_detail = response.text

        raise HTTPException(
            status_code=response.status_code,
            detail=error_detail or "Upload failed",
        )

    return response.json()


@router.get(
    "",
    response_model=list[DocumentResponse],
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's documents.
    """

    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
    )

    return result.scalars().all()


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get single document.
    """

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
    )

    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document