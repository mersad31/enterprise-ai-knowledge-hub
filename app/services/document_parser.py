import asyncio
from pathlib import Path
from io import BytesIO

import docx
from pypdf import PdfReader

from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """Parse uploaded files (PDF, DOCX, TXT) into raw text."""

    _parser = {
        ".pdf": "_parse_pdf",
        ".docx": "_parse_docx",
        ".txt": "_parse_txt",
    }

    async def parse(self, file_content: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()

        method_name = self._parser.get(ext)
        if not method_name:
            raise ValueError(f"Unsupported file type: {ext}")

        parser = getattr(self, method_name)

        try:
            text = await asyncio.to_thread(parser, file_content)
        except Exception as e:
            raise ValueError(f"Failed to parse file '{filename}': {e}") from e

        logger.info(
            "Document parsed successfully",
            extra={"filename": filename, "ext": ext, "text_length": len(text)}
        )

        return text.strip()


    def _parse_pdf(self, file_content: bytes) -> str:
        reader = PdfReader(BytesIO(file_content))
        texts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)

        return "\n".join(texts)

    def _parse_docx(self, file_content: bytes) -> str:
        doc = docx.Document(BytesIO(file_content))
        return "\n".join(
            p.text for p in doc.paragraphs if p.text and p.text.strip()
        )

    def _parse_txt(self, file_content: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Unable to decode text file")

