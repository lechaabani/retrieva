"""HTML content extractor using BeautifulSoup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from bs4 import BeautifulSoup

from core.exceptions import ExtractionError
from core.ingestion.extractors.base import BaseExtractor, ExtractedDocument

logger = logging.getLogger(__name__)

_REMOVE_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript"}


class HTMLExtractor(BaseExtractor):
    """Extracts readable text from HTML content using BeautifulSoup."""

    supported_extensions = [".html", ".htm"]

    async def extract(self, source: Union[str, Path, bytes]) -> ExtractedDocument:
        """Extract text from an HTML file, bytes, or raw HTML string.

        Strips scripts, styles, navigation, and other boilerplate tags before
        extracting visible text.

        Args:
            source: File path, raw HTML bytes, or an HTML string.

        Returns:
            ExtractedDocument with cleaned text.

        Raises:
            ExtractionError: If parsing fails.
        """
        try:
            html: str
            file_name = "page.html"

            if isinstance(source, bytes):
                html = source.decode("utf-8", errors="replace")
            elif isinstance(source, Path) or (isinstance(source, str) and Path(source).exists()):
                path = Path(source)
                html = path.read_text(encoding="utf-8", errors="replace")
                file_name = path.name
            else:
                # Treat as raw HTML string
                html = str(source)

            soup = BeautifulSoup(html, "html.parser")

            # Remove non-content tags
            for tag in soup.find_all(_REMOVE_TAGS):
                tag.decompose()

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else file_name

            # Get clean text
            text = soup.get_text(separator="\n", strip=True)
            # Collapse excessive blank lines
            lines = [line for line in text.splitlines() if line.strip()]
            content = "\n".join(lines)

            metadata = {
                "source_type": "html",
                "file_name": file_name,
                "char_count": len(content),
            }

            # Extract meta description if present
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                metadata["description"] = meta_desc["content"]

            logger.info("Extracted %d characters from HTML %s", len(content), file_name)
            return ExtractedDocument(content=content, metadata=metadata, title=title)

        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Failed to extract HTML: {exc}") from exc
