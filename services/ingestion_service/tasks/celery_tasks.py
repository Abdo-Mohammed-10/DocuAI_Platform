import asyncio
import uuid
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.celery_app import celery_app
from shared.db.session import AsyncSessionLocal
from shared.db.models.document import Document, DocumentStatus
from shared.db.models.chunk import Chunk
from services.ingestion_service.processors.pdf_processor import PDFProcessor
from services.ingestion_service.processors.chunker import TextChunker

logger = get_task_logger(__name__)

def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

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
        run_async(_process_document_async(document_id, file_bytes))
        logger.info(f"Document processed successfully: {document_id}")
        
    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {exc}")
        run_async(_update_document_status(
            document_id,
            DocumentStatus.FAILED,
            str(exc),
        ))
        
        raise self.retry(exc=exc)

async def _process_document_async(document_id: str, file_bytes: bytes):
    async with AsyncSessionLocal() as db:
        await _update_status(db, document_id, DocumentStatus.PROCESSING)
        
        # extract pages
        processor = PDFProcessor()
        pages = processor.extract_pages(file_bytes)
        logger.info(f"Extracted {len(pages)} pages from document {document_id}")
        
        # chunk pages
        chunker = TextChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk_pages(pages)
        logger.info(f"Created {len(chunks)} chunks")
        
        # save chunks
        doc_uuid = uuid.UUID(document_id)
        chunk_objs = [
            Chunk(
                document_id=doc_uuid,
                content=c.content,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                token_count=c.token_count,
            )
            for c in chunks
        ]
        
        db.add_all(chunk_objs)
        await _update_status(db, document_id, DocumentStatus.DONE)
        await db.commit()
        logger.info(f"Saved {len(chunks)} chunks to database for document {document_id}")

async def _update_status(
    db: AsyncSession,
    document_id: str,
    status: DocumentStatus,
    error: str = None,
):
    result = await db.execute(
        select(Document).where(Document.id == uuid.UUID(document_id))
    )
    
    doc = result.scalar_one_or_none()
    if doc:
        doc.status = status
        if error:
            doc.error_message = error
            
async def _update_document_status(document_id: str, status: DocumentStatus, error: str):
    async with AsyncSessionLocal() as db:
        await _update_status(db, document_id, status, error)
        await db.commit()  