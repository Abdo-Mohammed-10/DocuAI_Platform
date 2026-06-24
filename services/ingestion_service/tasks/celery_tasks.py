import asyncio
import time
import uuid

from celery.utils.log import get_task_logger
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.ingestion_service.processors.chunker import TextChunker
from services.ingestion_service.processors.pdf_processor import PDFProcessor
from services.vector_service.stores.pgvector_store import PGVectorStore
from shared.celery_app import celery_app
from shared.config import settings
from shared.db.models.chunk import Chunk
from shared.db.models.document import Document, DocumentStatus

logger = get_task_logger(__name__)


def _make_session():
    engine = create_async_engine(
        settings.database_url,
        pool_size=2,
        max_overflow=0,
    )
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return factory, engine


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="tasks.process_document",
)
def process_document(self, document_id: str, file_bytes_hex: str):
    try:
        file_bytes = bytes.fromhex(file_bytes_hex)
        asyncio.run(_process_document_async(document_id, file_bytes))
    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {exc}")
        asyncio.run(_set_status_safe(document_id, DocumentStatus.failed, str(exc)))
        raise self.retry(exc=exc)


# ── async pipeline ────────────────────────────────────────
async def _process_document_async(document_id: str, file_bytes: bytes):
    start_time = time.time()
    factory, engine = _make_session()

    try:
        async with factory() as db:
            await _set_status(db, document_id, DocumentStatus.processing)

            pages = PDFProcessor().extract_pages(file_bytes)
            chunks = TextChunker(chunk_size=500, overlap=50).chunk_pages(pages)

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
            await db.flush()
            logger.info(f"Created {len(chunk_objs)} chunks")

            # embed
            vector_store = PGVectorStore()
            embedded = await vector_store.save_embeddings(doc_uuid, db)
            logger.info(f"Embedded {embedded} chunks")

            await _set_status(db, document_id, DocumentStatus.done)
            await db.commit()

    finally:
        await engine.dispose()

    duration = time.time() - start_time
    logger.info(f"Document {document_id} processed in {duration:.2f}s")


# ── DB helpers ────────────────────────────────────────────
async def _set_status(db: AsyncSession, document_id: str, status: DocumentStatus, error: str = None):  # noqa: E501
    values = {"status": status}
    if error:
        values["error_message"] = error

    await db.execute(
        update(Document)
        .where(Document.id == uuid.UUID(document_id))
        .values(**values)
    )
    await db.flush()


async def _set_status_safe(document_id: str, status: DocumentStatus, error: str = None):
    factory, engine = _make_session()
    try:
        async with factory() as db:
            await _set_status(db, document_id, status, error)
            await db.commit()
    finally:
        await engine.dispose()