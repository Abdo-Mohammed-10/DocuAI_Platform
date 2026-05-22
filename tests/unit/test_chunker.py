from services.ingestion_service.processors.chunker import TextChunker
from services.ingestion_service.processors.pdf_processor import PageContent


def test_chunker_basic():
    pages = [
        PageContent(page_number=1, text=" ".join([f"word{i}" for i in range(600)]), char_count=3000)
    ]
    chunker = TextChunker(chunk_size=500, overlap=50)
    chunks = chunker.chunk_pages(pages)

    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 1


def test_chunker_token_count():
    pages = [
        PageContent(page_number=1, text="hello world foo bar", char_count=19)
    ]
    chunker = TextChunker(chunk_size=500, overlap=0)
    chunks = chunker.chunk_pages(pages)

    assert chunks[0].token_count == 4


def test_chunker_overlap():
    words = [f"w{i}" for i in range(20)]
    pages = [PageContent(page_number=1, text=" ".join(words), char_count=100)]
    chunker = TextChunker(chunk_size=10, overlap=3)
    chunks = chunker.chunk_pages(pages)

    first_end_words = set(chunks[0].content.split()[-3:])
    second_start_words = set(chunks[1].content.split()[:3])
    assert first_end_words == second_start_words