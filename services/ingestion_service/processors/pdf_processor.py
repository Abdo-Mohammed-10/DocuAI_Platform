from dataclasses import dataclass

import fitz


@dataclass
class PageContent:
    page_number: int
    text: str
    char_count: int


class PDFProcessor:
    def extract_pages(self, file_bytes: bytes) -> list[PageContent]:
        pages = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages.append(
                        PageContent(
                            page_number=page_num,
                            text=text,
                            char_count=len(text),
                        )
                    )
        return pages

    def get_metadata(self, file_bytes: bytes) -> dict:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            return {
                "page_count": len(doc),
                "metadata": doc.metadata,
            }