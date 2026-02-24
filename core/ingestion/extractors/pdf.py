"""PDF content extractor using PyPDF2."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Union

from PyPDF2 import PdfReader

from core.exceptions import ExtractionError
from core.ingestion.extractors.base import BaseExtractor, ExtractedDocument

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extracts text content from PDF files using PyPDF2."""

    supported_extensions = [".pdf"]

    async def extract(self, source: Union[str, Path, bytes]) -> ExtractedDocument:
        """Extract text from a PDF file or byte stream.

        Args:
            source: File path or raw PDF bytes.

        Returns:
            ExtractedDocument with concatenated page text.

        Raises:
            ExtractionError: If the PDF cannot be read or parsed.
        """
        try:
            if isinstance(source, bytes):
                reader = PdfReader(io.BytesIO(source))
                file_name = "uploaded.pdf"
            else:
                path = Path(source)
                if not path.exists():
                    raise ExtractionError(f"PDF file not found: {path}")
                reader = PdfReader(str(path))
                file_name = path.name

            pages: list[str] = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

            content = "\n\n".join(pages)

            metadata = {
                "source_type": "pdf",
                "file_name": file_name,
                "page_count": len(reader.pages),
            }
            if reader.metadata:
                if reader.metadata.title:
                    metadata["pdf_title"] = reader.metadata.title
                if reader.metadata.author:
                    metadata["pdf_author"] = reader.metadata.author

            title = (
                (reader.metadata.title if reader.metadata and reader.metadata.title else None)
                or file_name
            )

            logger.info("Extracted %d pages from PDF %s", len(reader.pages), file_name)
            return ExtractedDocument(content=content, metadata=metadata, title=title)

        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Failed to extract PDF: {exc}") from exc
