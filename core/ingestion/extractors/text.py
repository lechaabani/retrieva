"""Plain-text content extractor for TXT, Markdown, and CSV files."""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Union

from core.exceptions import ExtractionError
from core.ingestion.extractors.base import BaseExtractor, ExtractedDocument

logger = logging.getLogger(__name__)


class TextExtractor(BaseExtractor):
    """Extracts content from plain-text, Markdown, and CSV files."""

    supported_extensions = [".txt", ".md", ".csv", ".log", ".rst"]

    async def extract(self, source: Union[str, Path, bytes]) -> ExtractedDocument:
        """Extract text from a plain-text file or byte stream.

        CSV files are converted to pipe-delimited table text.

        Args:
            source: File path or raw bytes (assumed UTF-8).

        Returns:
            ExtractedDocument with the file contents.

        Raises:
            ExtractionError: If the file cannot be read.
        """
        try:
            if isinstance(source, bytes):
                text = source.decode("utf-8", errors="replace")
                file_name = "uploaded.txt"
                extension = ".txt"
            else:
                path = Path(source)
                if not path.exists():
                    raise ExtractionError(f"Text file not found: {path}")
                text = path.read_text(encoding="utf-8", errors="replace")
                file_name = path.name
                extension = path.suffix.lower()

            source_type = "text"
            if extension == ".csv":
                text = self._csv_to_text(text)
                source_type = "csv"
            elif extension == ".md":
                source_type = "markdown"

            metadata = {
                "source_type": source_type,
                "file_name": file_name,
                "char_count": len(text),
            }

            title = Path(file_name).stem if file_name else "Untitled"

            logger.info("Extracted %d characters from %s", len(text), file_name)
            return ExtractedDocument(content=text, metadata=metadata, title=title)

        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Failed to extract text file: {exc}") from exc

    @staticmethod
    def _csv_to_text(raw: str) -> str:
        """Convert CSV content to a pipe-delimited table string."""
        reader = csv.reader(io.StringIO(raw))
        rows = [" | ".join(row) for row in reader if any(cell.strip() for cell in row)]
        return "\n".join(rows)
