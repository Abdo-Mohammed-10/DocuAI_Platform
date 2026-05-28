import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from services.nlp_service.pipelines.rag_pipeline import RAGPipeline
from shared.db.models.chunk import Chunk


def make_chunk(index: int, content: str, page: int = 1) -> Chunk:
    c = Chunk()
    c.chunk_index = index
    c.page_number = page
    c.content = content
    c.token_count = len(content.split())
    return c


def test_select_relevant_scores_by_keyword():
    pipeline = RAGPipeline(top_k=2)
    chunks = [
        make_chunk(0, "the cat sat on the mat"),
        make_chunk(1, "machine learning is great"),
        make_chunk(2, "the cat ate the fish"),
    ]
    result = pipeline._select_relevant("cat mat", chunks)
    assert len(result) == 2
    assert result[0].content == "the cat sat on the mat"


def test_select_relevant_top_k_limit():
    pipeline = RAGPipeline(top_k=2)
    chunks = [make_chunk(i, f"word{i} common") for i in range(10)]
    result = pipeline._select_relevant("common", chunks)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_run_returns_no_content_when_no_chunks():
    pipeline = RAGPipeline()
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await pipeline.run(
        question="What is this about?",
        document_id=uuid.uuid4(),
        db=mock_db,
    )
    assert "No content" in result.answer