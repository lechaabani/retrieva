"""File upload connector for local files and uploaded file objects."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Union

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, UnsupportedFileTypeError
from core.ingestion.extractors.base import BaseExtractor
from core.ingestion.extractors.docx import DocxExtractor
from core.ingestion.extractors.excel import ExcelExtractor
from core.ingestion.extractors.html import HTMLExtractor
from core.ingestion.extractors.pdf import PDFExtractor
from core.ingestion.extractors.text import TextExtractor

logger = logging.getLogger(__name__)

_EXTRACTOR_REGISTRY: dict[str, type[BaseExtractor]] = {
    ".pdf": PDFExtractor,
    ".docx": DocxExtractor,
    ".xlsx": ExcelExtractor,
    ".xls": ExcelExtractor,
    ".txt": TextExtractor,
    ".md": TextExtractor,
    ".csv": TextExtractor,
    ".log": TextExtractor,
    ".rst": TextExtractor,
    ".html": HTMLExtractor,
    ".htm": HTMLExtractor,
}


class FileUploadConnector(BaseConnector):
    """Connector for local files or uploaded file objects.

    Detects file type and delegates to the appropriate extractor.
    """

    name = "file_upload"

    def __init__(
        self,
        file_path: Union[str, Path, None] = None,
        file_bytes: bytes | None = None,
        file_name: str | None = None,
    ) -> None:
        """
        Args:
            file_path: Path to a local file.
            file_bytes: Raw file bytes (e.g. from an upload).
            file_name: Original filename (required if using file_bytes).
        """
        self.file_path = Path(file_path) if file_path else None
        self.file_bytes = file_bytes
        self.file_name = file_name

    async def pull(self) -> list[Document]:
        """Extract the file content and return it as a Document.

        Returns:
            A single-element list with the extracted Document.

        Raises:
            ConnectorError: If neither file_path nor file_bytes is provided.
            UnsupportedFileTypeError: If the file type is not supported.
        """
        try:
            if self.file_path:
                ext = self.file_path.suffix.lower()
                source = self.file_path
                name = self.file_path.name
            elif self.file_bytes and self.file_name:
                ext = Path(self.file_name).suffix.lower()
                source = self.file_bytes
                name = self.file_name
            else:
                raise ConnectorError("Provide either file_path or (file_bytes + file_name)")

            if ext not in _EXTRACTOR_REGISTRY:
                raise UnsupportedFileTypeError(f"No extractor for extension '{ext}'")

            extractor = _EXTRACTOR_REGISTRY[ext]()
            extracted = await extractor.extract(source)

            doc = Document(
                content=extracted.content,
                title=extracted.title or name,
                source=str(self.file_path or name),
                metadata={**extracted.metadata, "connector": self.name},
            )

            logger.info("FileUploadConnector extracted document: %s", name)
            return [doc]

        except (ConnectorError, UnsupportedFileTypeError):
            raise
        except Exception as exc:
            raise ConnectorError(f"File upload extraction failed: {exc}") from exc

    async def test_connection(self) -> bool:
        if self.file_path:
            return self.file_path.exists()
        return self.file_bytes is not None
