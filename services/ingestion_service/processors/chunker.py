from dataclasses import dataclass

from services.ingestion_service.processors.pdf_processor import PageContent

@dataclass
class TextChunk:
    content: str
    page_number: int
    chunk_index: int
    token_count: int
    embedding: str

class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_pages(self, pages: list[PageContent]) -> list[TextChunk]:
        chunks = []
        chunk_index = 0

        for page in pages:
            words = page.text.split()
            start = 0

            while start < len(words):
                end = start + self.chunk_size
                chunk_words = words[start:end]
                content = " ".join(chunk_words)

                chunks.append(
                    TextChunk(
                        content=content,
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        token_count=len(chunk_words),
                        embedding="[]",
                    )
                )

                chunk_index += 1
                start += self.chunk_size - self.overlap

        return chunks
