"""Unit tests for content extractors."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from core.exceptions import ExtractionError
from core.ingestion.extractors.base import ExtractedDocument
from core.ingestion.extractors.text import TextExtractor
from core.ingestion.extractors.html import HTMLExtractor


# =============================================================================
# TextExtractor
# =============================================================================

class TestTextExtractor:
    """Tests for the plain-text, Markdown, and CSV extractor."""

    @pytest.fixture
    def extractor(self) -> TextExtractor:
        return TextExtractor()

    async def test_extract_txt_file(self, extractor, temp_files):
        """Extracting a .txt file should return its full content."""
        result = await extractor.extract(temp_files["txt"])

        assert isinstance(result, ExtractedDocument)
        assert "plain text test file" in result.content
        assert result.metadata["source_type"] == "text"
        assert result.metadata["file_name"] == "sample.txt"
        assert result.title == "sample"
        assert not result.is_empty

    async def test_extract_md_file(self, extractor, temp_files):
        """Extracting a .md file should return raw Markdown content."""
        result = await extractor.extract(temp_files["md"])

        assert "# Test Heading" in result.content
        assert "**markdown**" in result.content
        assert result.metadata["source_type"] == "markdown"

    async def test_extract_csv_file(self, extractor, temp_files):
        """Extracting a .csv file should convert it to pipe-delimited text."""
        result = await extractor.extract(temp_files["csv"])

        assert "name | age | city" in result.content
        assert "Alice | 30 | Paris" in result.content
        assert result.metadata["source_type"] == "csv"

    async def test_extract_from_bytes(self, extractor):
        """Extracting from raw bytes should decode as UTF-8."""
        content = b"Hello from bytes content"
        result = await extractor.extract(content)

        assert result.content == "Hello from bytes content"
        assert result.metadata["file_name"] == "uploaded.txt"

    async def test_extract_nonexistent_file_raises(self, extractor):
        """Extracting a file that does not exist should raise ExtractionError."""
        with pytest.raises(ExtractionError, match="not found"):
            await extractor.extract("/nonexistent/path/file.txt")

    async def test_can_handle_supported_extensions(self, extractor):
        """The extractor should report support for .txt, .md, .csv, .log, .rst."""
        assert extractor.can_handle(".txt")
        assert extractor.can_handle(".md")
        assert extractor.can_handle(".csv")
        assert extractor.can_handle(".log")
        assert not extractor.can_handle(".pdf")
        assert not extractor.can_handle(".docx")

    async def test_char_count_in_metadata(self, extractor, temp_files):
        """Metadata should include char_count reflecting the content length."""
        result = await extractor.extract(temp_files["txt"])
        assert result.metadata["char_count"] == len(result.content)


# =============================================================================
# HTMLExtractor
# =============================================================================

class TestHTMLExtractor:
    """Tests for the HTML content extractor."""

    @pytest.fixture
    def extractor(self) -> HTMLExtractor:
        return HTMLExtractor()

    async def test_strips_tags_extracts_text(self, extractor, temp_files):
        """HTML tags should be stripped; only visible text should remain."""
        result = await extractor.extract(temp_files["html"])

        assert isinstance(result, ExtractedDocument)
        assert "Hello World" in result.content
        assert "test HTML content" in result.content
        assert "<h1>" not in result.content
        assert "<p>" not in result.content

    async def test_removes_script_tags(self, extractor, temp_files):
        """Script content should be removed entirely."""
        result = await extractor.extract(temp_files["html"])
        assert "alert" not in result.content

    async def test_removes_nav_tags(self, extractor, temp_files):
        """Navigation elements should be removed."""
        result = await extractor.extract(temp_files["html"])
        assert "Navigation content" not in result.content

    async def test_extracts_title(self, extractor, temp_files):
        """The page title should be extracted from the <title> tag."""
        result = await extractor.extract(temp_files["html"])
        assert result.title == "Test Page"

    async def test_extract_from_html_string(self, extractor):
        """Passing a raw HTML string (not a file path) should work."""
        html = "<html><body><p>Direct HTML string</p></body></html>"
        result = await extractor.extract(html)

        assert "Direct HTML string" in result.content
        assert result.metadata["source_type"] == "html"

    async def test_extract_from_bytes(self, extractor):
        """Extracting from HTML bytes should decode and parse correctly."""
        html_bytes = b"<html><body><p>Bytes HTML</p></body></html>"
        result = await extractor.extract(html_bytes)

        assert "Bytes HTML" in result.content

    async def test_can_handle_supported_extensions(self, extractor):
        """The extractor should report support for .html and .htm."""
        assert extractor.can_handle(".html")
        assert extractor.can_handle(".htm")
        assert not extractor.can_handle(".txt")
        assert not extractor.can_handle(".pdf")

    async def test_meta_description_extraction(self, extractor):
        """Meta description should be included in metadata when present."""
        html = (
            '<html><head><meta name="description" content="A test description">'
            "</head><body><p>Content</p></body></html>"
        )
        result = await extractor.extract(html)
        assert result.metadata.get("description") == "A test description"


# =============================================================================
# PDFExtractor (mocked)
# =============================================================================

class TestPDFExtractor:
    """Tests for the PDF extractor using mocked PyPDF2."""

    async def test_extract_from_file_path(self):
        """PDF extraction from a file path should concatenate page text."""
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = "Page one content."
        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = "Page two content."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page_1, mock_page_2]
        mock_reader.metadata = MagicMock()
        mock_reader.metadata.title = "Test PDF"
        mock_reader.metadata.author = "Test Author"

        with (
            patch("core.ingestion.extractors.pdf.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
        ):
            from core.ingestion.extractors.pdf import PDFExtractor

            extractor = PDFExtractor()
            result = await extractor.extract("/fake/path/test.pdf")

        assert "Page one content." in result.content
        assert "Page two content." in result.content
        assert result.metadata["source_type"] == "pdf"
        assert result.metadata["page_count"] == 2
        assert result.title == "Test PDF"

    async def test_extract_from_bytes(self):
        """PDF extraction from bytes should use BytesIO."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted from bytes."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None

        with patch("core.ingestion.extractors.pdf.PdfReader", return_value=mock_reader):
            from core.ingestion.extractors.pdf import PDFExtractor

            extractor = PDFExtractor()
            result = await extractor.extract(b"fake-pdf-bytes")

        assert result.content == "Extracted from bytes."
        assert result.metadata["file_name"] == "uploaded.pdf"

    async def test_nonexistent_file_raises(self):
        """Extracting a non-existent PDF should raise ExtractionError."""
        from core.ingestion.extractors.pdf import PDFExtractor

        extractor = PDFExtractor()
        with pytest.raises(ExtractionError, match="not found"):
            await extractor.extract("/nonexistent/file.pdf")

    def test_can_handle_pdf(self):
        """The PDF extractor should only handle .pdf files."""
        from core.ingestion.extractors.pdf import PDFExtractor

        extractor = PDFExtractor()
        assert extractor.can_handle(".pdf")
        assert not extractor.can_handle(".docx")


# =============================================================================
# DocxExtractor (mocked)
# =============================================================================

class TestDocxExtractor:
    """Tests for the DOCX extractor using mocked python-docx."""

    async def test_extract_from_file_path(self):
        """DOCX extraction should join paragraph text with double newlines."""
        mock_para_1 = MagicMock()
        mock_para_1.text = "First paragraph."
        mock_para_2 = MagicMock()
        mock_para_2.text = "Second paragraph."
        mock_para_3 = MagicMock()
        mock_para_3.text = ""  # empty paragraph should be skipped

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para_1, mock_para_2, mock_para_3]
        mock_doc.tables = []
        mock_doc.core_properties = MagicMock()
        mock_doc.core_properties.title = "Test DOCX"
        mock_doc.core_properties.author = "Author Name"

        with (
            patch("core.ingestion.extractors.docx.DocxDocument", return_value=mock_doc),
            patch("pathlib.Path.exists", return_value=True),
        ):
            from core.ingestion.extractors.docx import DocxExtractor

            extractor = DocxExtractor()
            result = await extractor.extract("/fake/path/test.docx")

        assert "First paragraph." in result.content
        assert "Second paragraph." in result.content
        assert result.metadata["source_type"] == "docx"
        assert result.title == "Test DOCX"
        assert result.metadata.get("author") == "Author Name"

    async def test_extract_tables(self):
        """Table rows should be included as pipe-delimited text."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        mock_cell_1 = MagicMock()
        mock_cell_1.text = "Name"
        mock_cell_2 = MagicMock()
        mock_cell_2.text = "Age"
        mock_row = MagicMock()
        mock_row.cells = [mock_cell_1, mock_cell_2]
        mock_table = MagicMock()
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]
        mock_doc.core_properties = MagicMock()
        mock_doc.core_properties.title = None
        mock_doc.core_properties.author = None

        with (
            patch("core.ingestion.extractors.docx.DocxDocument", return_value=mock_doc),
            patch("pathlib.Path.exists", return_value=True),
        ):
            from core.ingestion.extractors.docx import DocxExtractor

            extractor = DocxExtractor()
            result = await extractor.extract("/fake/path/tables.docx")

        assert "Name | Age" in result.content

    async def test_extract_from_bytes(self):
        """DOCX extraction from bytes should work via BytesIO."""
        mock_para = MagicMock()
        mock_para.text = "Byte-based content."
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        mock_doc.core_properties = MagicMock()
        mock_doc.core_properties.title = None
        mock_doc.core_properties.author = None

        with patch("core.ingestion.extractors.docx.DocxDocument", return_value=mock_doc):
            from core.ingestion.extractors.docx import DocxExtractor

            extractor = DocxExtractor()
            result = await extractor.extract(b"fake-docx-bytes")

        assert result.content == "Byte-based content."
        assert result.metadata["file_name"] == "uploaded.docx"

    def test_can_handle_docx(self):
        """The DOCX extractor should only handle .docx files."""
        from core.ingestion.extractors.docx import DocxExtractor

        extractor = DocxExtractor()
        assert extractor.can_handle(".docx")
        assert not extractor.can_handle(".doc")
        assert not extractor.can_handle(".pdf")
