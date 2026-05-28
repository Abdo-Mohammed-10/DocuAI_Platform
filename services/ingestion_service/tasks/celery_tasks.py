import asyncio
import uuid

from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.ingestion_service.processors.chunker import TextChunker
from services.ingestion_service.processors.pdf_processor import PDFProcessor
from shared.celery_app import celery_app
from shared.db.models.chunk import Chunk
from shared.db.models.document import Document, DocumentStatus
from shared.db.session import AsyncSessionLocal

logger = get_task_logger(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def run_async(coro):
    return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="tasks.process_document",
)
def process_document(self, document_id: str, file_bytes_hex: str):
    try:
        logger.info(f"Processing document: {document_id}")

        file_bytes = bytes.fromhex(file_bytes_hex)

        run_async(
            _process_document_async(
                document_id=document_id,
                file_bytes=file_bytes,
            )
        )

        logger.info(f"Document processed successfully: {document_id}")

    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {exc}")

        run_async(
            _update_document_status(
                document_id=document_id,
                status=DocumentStatus.FAILED,
                error=str(exc),
            )
        )

        raise self.retry(exc=exc)


async def _process_document_async(
    document_id: str,
    file_bytes: bytes,
):
    async with AsyncSessionLocal() as db:
        await _update_status(
            db=db,
            document_id=document_id,
            status=DocumentStatus.PROCESSING,
        )

        # Extract pages from PDF
        processor = PDFProcessor()
        pages = processor.extract_pages(file_bytes)

        logger.info(f"Extracted {len(pages)} pages from document {document_id}")

        # Chunk text
        chunker = TextChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk_pages(pages)

        logger.info(f"Created {len(chunks)} chunks")

        # Save chunks
        doc_uuid = uuid.UUID(document_id)

        chunk_objects = [
            Chunk(
                document_id=doc_uuid,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                embedding=chunk.embedding,
            )
            for chunk in chunks
        ]

        db.add_all(chunk_objects)

        await _update_status(
            db=db,
            document_id=document_id,
            status=DocumentStatus.DONE,
        )

        await db.commit()

        logger.info(
            f"Saved {len(chunks)} chunks to database " f"for document {document_id}"
        )


async def _update_status(
    db: AsyncSession,
    document_id: str,
    status: DocumentStatus,
    error: str | None = None,
):
    result = await db.execute(
        select(Document).where(Document.id == uuid.UUID(document_id))
    )

    document = result.scalar_one_or_none()

    if document:
        document.status = status

        if error:
            document.error_message = error


async def _update_document_status(
    document_id: str,
    status: DocumentStatus,
    error: str | None = None,
):
    async with AsyncSessionLocal() as db:
        await _update_status(
            db=db,
            document_id=document_id,
            status=status,
            error=error,
        )

        await db.commit()
