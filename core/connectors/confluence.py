"""Confluence connector using the Confluence REST API (Cloud & Server)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)


class ConfluenceConnector(BaseConnector):
    """Connector for Atlassian Confluence via REST API.

    Supports:
    * Confluence Cloud (api.atlassian.com) and Server/Data Center.
    * Fetching all pages from one or more spaces.
    * Fetching specific pages by ID.
    * Extracting page body content as plain text (strips HTML).
    * Pagination through large spaces.
    * Basic auth (email + API token) and bearer token auth.
    """

    name = "confluence"

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        bearer_token: Optional[str] = None,
        space_keys: Optional[list[str]] = None,
        page_ids: Optional[list[str]] = None,
        include_attachments: bool = False,
        max_pages: int = 200,
        cql: Optional[str] = None,
    ) -> None:
        """
        Args:
            base_url: Confluence instance URL (e.g. https://myorg.atlassian.net/wiki).
            username: Email / username for basic auth.
            api_token: Confluence API token (used with username).
            bearer_token: Bearer token for OAuth / PAT authentication.
            space_keys: List of space keys to pull pages from.
            page_ids: Specific page IDs to fetch.
            include_attachments: Whether to include file attachments.
            max_pages: Maximum number of pages to retrieve.
            cql: Custom CQL query string to filter pages.
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.bearer_token = bearer_token
        self.space_keys = space_keys or []
        self.page_ids = page_ids or []
        self.include_attachments = include_attachments
        self.max_pages = max_pages
        self.cql = cql

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth(self):
        """Build httpx auth tuple or headers."""
        if self.username and self.api_token:
            return (self.username, self.api_token)
        return None

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        return headers

    def _api_url(self, path: str) -> str:
        return f"{self.base_url}/rest/api{path}"

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Strip HTML tags and return plain text."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Remove script/style elements
            for tag in soup.find_all(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            # Fallback: very basic tag stripping
            import re
            clean = re.sub(r"<[^>]+>", " ", html)
            return re.sub(r"\s+", " ", clean).strip()

    async def _get_page_content(self, client, page_id: str) -> Optional[dict[str, Any]]:
        """Fetch a single page with body content expanded."""
        resp = await client.get(
            self._api_url(f"/content/{page_id}"),
            headers=self._headers(),
            auth=self._auth(),
            params={"expand": "body.storage,version,space,ancestors"},
        )
        if resp.status_code == 404:
            logger.warning("Confluence page %s not found", page_id)
            return None
        resp.raise_for_status()
        return resp.json()

    async def _search_pages(
        self, client, cql: str, limit: int
    ) -> list[dict[str, Any]]:
        """Search for pages using CQL with pagination."""
        pages: list[dict[str, Any]] = []
        start = 0

        while len(pages) < limit:
            batch_size = min(50, limit - len(pages))
            resp = await client.get(
                self._api_url("/content/search"),
                headers=self._headers(),
                auth=self._auth(),
                params={
                    "cql": cql,
                    "limit": batch_size,
                    "start": start,
                    "expand": "body.storage,version,space",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                break

            pages.extend(results)
            start += len(results)

            # Check if more results available
            if data.get("size", 0) < batch_size:
                break

        return pages

    async def _get_space_pages(self, client, space_key: str) -> list[dict[str, Any]]:
        """Fetch all pages from a Confluence space with pagination."""
        pages: list[dict[str, Any]] = []
        start = 0

        while len(pages) < self.max_pages:
            batch_size = min(50, self.max_pages - len(pages))
            resp = await client.get(
                self._api_url("/content"),
                headers=self._headers(),
                auth=self._auth(),
                params={
                    "spaceKey": space_key,
                    "type": "page",
                    "limit": batch_size,
                    "start": start,
                    "expand": "body.storage,version,space",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                break

            pages.extend(results)
            start += len(results)

            if data.get("size", 0) < batch_size:
                break

        return pages

    def _page_to_document(self, page: dict[str, Any]) -> Optional[Document]:
        """Convert a Confluence page JSON to a Document."""
        title = page.get("title", "Untitled")
        page_id = page.get("id", "")

        body_html = ""
        body = page.get("body", {})
        if "storage" in body:
            body_html = body["storage"].get("value", "")

        content = self._html_to_text(body_html)
        if not content.strip():
            logger.debug("Skipping empty page: %s (%s)", title, page_id)
            return None

        space_key = ""
        space = page.get("space", {})
        if space:
            space_key = space.get("key", "")

        # Build page URL
        links = page.get("_links", {})
        web_link = links.get("webui", "")
        if web_link and not web_link.startswith("http"):
            base = links.get("base", self.base_url)
            web_link = f"{base}{web_link}"
        source = web_link or f"{self.base_url}/pages/viewpage.action?pageId={page_id}"

        version = page.get("version", {})

        return Document(
            content=content,
            title=title,
            source=source,
            metadata={
                "connector": self.name,
                "confluence_page_id": page_id,
                "space_key": space_key,
                "version": version.get("number", 1),
                "last_modified_by": version.get("by", {}).get("displayName", ""),
                "last_modified": version.get("when", ""),
            },
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull documents from Confluence.

        Returns:
            List of Document instances extracted from Confluence pages.

        Raises:
            ConnectorError: On authentication or API errors.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                raw_pages: list[dict[str, Any]] = []

                # 1. Fetch specific pages by ID
                for pid in self.page_ids:
                    page = await self._get_page_content(client, pid)
                    if page:
                        raw_pages.append(page)

                # 2. Custom CQL query
                if self.cql:
                    cql_pages = await self._search_pages(
                        client, self.cql, self.max_pages - len(raw_pages)
                    )
                    raw_pages.extend(cql_pages)

                # 3. Fetch from space keys
                for space_key in self.space_keys:
                    space_pages = await self._get_space_pages(client, space_key)
                    raw_pages.extend(space_pages)

                # 4. If nothing configured, search for all pages
                if not self.page_ids and not self.cql and not self.space_keys:
                    raw_pages = await self._search_pages(
                        client,
                        "type = page ORDER BY lastModified DESC",
                        self.max_pages,
                    )

                logger.info("Confluence: found %d pages to process", len(raw_pages))

                documents: list[Document] = []
                seen_ids: set[str] = set()
                for page in raw_pages:
                    pid = page.get("id", "")
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)

                    doc = self._page_to_document(page)
                    if doc:
                        documents.append(doc)
                    if len(documents) >= self.max_pages:
                        break

                logger.info("Confluence: extracted %d documents", len(documents))
                return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"Confluence pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test connectivity by fetching Confluence server info.

        Returns:
            True if the API responds successfully.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    self._api_url("/space"),
                    headers=self._headers(),
                    auth=self._auth(),
                    params={"limit": 1},
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            raise ConnectionTestFailedError(
                f"Confluence connection test failed: {exc}"
            ) from exc
