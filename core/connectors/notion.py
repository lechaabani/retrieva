"""Notion connector using the Notion API v1."""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)

_NOTION_API_VERSION = "2022-06-28"
_NOTION_BASE = "https://api.notion.com/v1"


class NotionConnector(BaseConnector):
    """Connector for Notion workspaces via the official Notion API.

    Supports:
    * Pulling all pages accessible by the integration.
    * Pulling pages from a specific database.
    * Extracting rich-text block content as plain text.
    * Pagination through large result sets.
    """

    name = "notion"

    def __init__(
        self,
        api_key: str,
        database_ids: Optional[list[str]] = None,
        page_ids: Optional[list[str]] = None,
        max_pages: int = 200,
        include_databases: bool = True,
    ) -> None:
        """
        Args:
            api_key: Notion internal integration token (secret_xxx).
            database_ids: Specific database IDs to query pages from.
            page_ids: Specific page IDs to fetch directly.
            max_pages: Maximum number of pages to retrieve.
            include_databases: If True and no database_ids given, search for
                all databases and pull their pages.
        """
        self.api_key = api_key
        self.database_ids = database_ids or []
        self.page_ids = page_ids or []
        self.max_pages = max_pages
        self.include_databases = include_databases

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": _NOTION_API_VERSION,
            "Content-Type": "application/json",
        }

    async def _search_pages(self, client) -> list[dict[str, Any]]:
        """Search all pages accessible by the integration."""
        pages: list[dict[str, Any]] = []
        start_cursor: Optional[str] = None

        while len(pages) < self.max_pages:
            body: dict[str, Any] = {
                "filter": {"property": "object", "value": "page"},
                "page_size": min(100, self.max_pages - len(pages)),
            }
            if start_cursor:
                body["start_cursor"] = start_cursor

            resp = await client.post(
                f"{_NOTION_BASE}/search",
                headers=self._headers(),
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

            pages.extend(data.get("results", []))

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

        return pages

    async def _query_database(self, client, database_id: str) -> list[dict[str, Any]]:
        """Query all pages from a Notion database."""
        pages: list[dict[str, Any]] = []
        start_cursor: Optional[str] = None

        while len(pages) < self.max_pages:
            body: dict[str, Any] = {
                "page_size": min(100, self.max_pages - len(pages)),
            }
            if start_cursor:
                body["start_cursor"] = start_cursor

            resp = await client.post(
                f"{_NOTION_BASE}/databases/{database_id}/query",
                headers=self._headers(),
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

            pages.extend(data.get("results", []))

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

        return pages

    async def _get_page(self, client, page_id: str) -> dict[str, Any]:
        """Retrieve a single page object."""
        resp = await client.get(
            f"{_NOTION_BASE}/pages/{page_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def _get_page_blocks(self, client, block_id: str) -> list[dict[str, Any]]:
        """Retrieve all child blocks of a page/block with pagination."""
        blocks: list[dict[str, Any]] = []
        start_cursor: Optional[str] = None

        while True:
            params: dict[str, Any] = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor

            resp = await client.get(
                f"{_NOTION_BASE}/blocks/{block_id}/children",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            blocks.extend(data.get("results", []))

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

        return blocks

    def _extract_rich_text(self, rich_text_array: list[dict]) -> str:
        """Convert a Notion rich_text array to plain text."""
        parts: list[str] = []
        for rt in rich_text_array:
            parts.append(rt.get("plain_text", ""))
        return "".join(parts)

    async def _blocks_to_text(self, client, block_id: str, depth: int = 0) -> str:
        """Recursively extract text from page blocks."""
        blocks = await self._get_page_blocks(client, block_id)
        lines: list[str] = []
        indent = "  " * depth

        for block in blocks:
            btype = block.get("type", "")
            block_data = block.get(btype, {})

            # Extract text from the block's rich_text field
            text = ""
            if "rich_text" in block_data:
                text = self._extract_rich_text(block_data["rich_text"])
            elif "text" in block_data:
                text = self._extract_rich_text(block_data["text"])

            if btype.startswith("heading_"):
                level = btype.replace("heading_", "")
                prefix = "#" * int(level) + " " if level.isdigit() else "## "
                lines.append(f"{prefix}{text}")
            elif btype in ("bulleted_list_item", "numbered_list_item"):
                lines.append(f"{indent}- {text}")
            elif btype == "to_do":
                checked = block_data.get("checked", False)
                marker = "[x]" if checked else "[ ]"
                lines.append(f"{indent}{marker} {text}")
            elif btype == "code":
                language = block_data.get("language", "")
                lines.append(f"```{language}\n{text}\n```")
            elif btype == "quote":
                lines.append(f"> {text}")
            elif btype == "divider":
                lines.append("---")
            elif btype == "table_row":
                cells = block_data.get("cells", [])
                row_texts = [self._extract_rich_text(cell) for cell in cells]
                lines.append("| " + " | ".join(row_texts) + " |")
            elif text:
                lines.append(f"{indent}{text}")

            # Recurse into children
            if block.get("has_children"):
                child_text = await self._blocks_to_text(client, block["id"], depth + 1)
                if child_text:
                    lines.append(child_text)

        return "\n".join(lines)

    def _extract_page_title(self, page: dict[str, Any]) -> str:
        """Extract the title from a Notion page object."""
        props = page.get("properties", {})
        for prop_name, prop_data in props.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                return self._extract_rich_text(title_array)
        return page.get("id", "Untitled")

    def _page_url(self, page: dict[str, Any]) -> str:
        """Build the Notion URL for a page."""
        return page.get("url", f"https://notion.so/{page.get('id', '')}")

    async def _process_page(self, client, page: dict[str, Any]) -> Optional[Document]:
        """Convert a Notion page to a Document."""
        page_id = page["id"]
        title = self._extract_page_title(page)

        try:
            content = await self._blocks_to_text(client, page_id)
            if not content.strip():
                logger.debug("Skipping empty page: %s (%s)", title, page_id)
                return None

            return Document(
                content=content,
                title=title,
                source=self._page_url(page),
                metadata={
                    "connector": self.name,
                    "notion_page_id": page_id,
                    "last_edited_time": page.get("last_edited_time", ""),
                    "created_time": page.get("created_time", ""),
                },
            )
        except Exception as exc:
            logger.warning("Failed to extract page %s (%s): %s", title, page_id, exc)
            return None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull documents from Notion.

        Returns:
            List of Document instances extracted from Notion pages.

        Raises:
            ConnectorError: On authentication or API errors.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                pages: list[dict[str, Any]] = []

                # 1. Fetch specific pages by ID
                for pid in self.page_ids:
                    try:
                        page = await self._get_page(client, pid)
                        pages.append(page)
                    except Exception as exc:
                        logger.warning("Failed to fetch page %s: %s", pid, exc)

                # 2. Query specific databases
                for db_id in self.database_ids:
                    try:
                        db_pages = await self._query_database(client, db_id)
                        pages.extend(db_pages)
                    except Exception as exc:
                        logger.warning("Failed to query database %s: %s", db_id, exc)

                # 3. If no specific IDs given, search all accessible pages
                if not self.page_ids and not self.database_ids:
                    pages = await self._search_pages(client)

                logger.info("Notion: found %d pages to process", len(pages))

                documents: list[Document] = []
                for page in pages[: self.max_pages]:
                    doc = await self._process_page(client, page)
                    if doc:
                        documents.append(doc)

                logger.info("Notion: extracted %d documents", len(documents))
                return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"Notion pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test the Notion API connection by listing the integration's bot user.

        Returns:
            True if the API responds successfully.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{_NOTION_BASE}/users/me",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            raise ConnectionTestFailedError(f"Notion connection test failed: {exc}") from exc
