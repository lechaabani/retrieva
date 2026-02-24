"""Generic REST API connector with configurable endpoints and parsing."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional, Union

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)


class RestAPIConnector(BaseConnector):
    """Generic, configurable connector for pulling documents from any REST API.

    Supports:
    * GET and POST requests with configurable headers and auth.
    * Bearer token, basic auth, API key (header or query param) authentication.
    * JSON and XML response parsing with configurable JSONPath-like extraction.
    * Multiple pagination strategies: offset, page number, cursor, Link header.
    * Configurable field mapping for content, title, and source.
    * Multiple endpoints in a single connector instance.
    """

    name = "rest_api"

    def __init__(
        self,
        base_url: str,
        endpoints: Optional[list[dict[str, Any]]] = None,
        auth_type: Optional[str] = None,
        auth_token: Optional[str] = None,
        auth_username: Optional[str] = None,
        auth_password: Optional[str] = None,
        api_key_header: Optional[str] = None,
        api_key_value: Optional[str] = None,
        api_key_query_param: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        max_pages: int = 50,
        verify_ssl: bool = True,
    ) -> None:
        """
        Args:
            base_url: Base URL for the API (e.g. "https://api.example.com/v1").
            endpoints: List of endpoint configs, each a dict with keys:
                - path: URL path relative to base_url (e.g. "/articles").
                - method: HTTP method, default "GET".
                - params: Query parameters dict.
                - body: Request body (for POST).
                - items_path: Dot-separated path to the list of items in the response
                    (e.g. "data.results" for {"data": {"results": [...]}}).
                - content_field: Field name or dot-path for document content.
                - title_field: Field name or dot-path for document title.
                - source_field: Field name or dot-path for document source URL.
                - metadata_fields: List of field names to include in metadata.
                - pagination: Pagination config dict with keys:
                    - type: "offset", "page", "cursor", or "link_header".
                    - param: Query parameter name for offset/page/cursor.
                    - limit_param: Parameter name for page size.
                    - limit: Items per page.
                    - cursor_path: Dot-path to next cursor in response.
                    - total_path: Dot-path to total count.
                    - max_pages: Override global max_pages for this endpoint.
            auth_type: Authentication type: "bearer", "basic", "api_key".
            auth_token: Bearer token value.
            auth_username: Username for basic auth.
            auth_password: Password for basic auth.
            api_key_header: Header name for API key auth (e.g. "X-API-Key").
            api_key_value: API key value.
            api_key_query_param: Query parameter name for API key.
            headers: Additional headers to include in all requests.
            timeout: HTTP request timeout in seconds.
            max_pages: Default maximum pages for pagination.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints or [{"path": "/", "method": "GET"}]
        self.auth_type = auth_type
        self.auth_token = auth_token
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.api_key_header = api_key_header
        self.api_key_value = api_key_value
        self.api_key_query_param = api_key_query_param
        self.custom_headers = headers or {}
        self.timeout = timeout
        self.max_pages = max_pages
        self.verify_ssl = verify_ssl

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        """Build request headers including auth."""
        hdrs: dict[str, str] = {
            "Accept": "application/json",
            **self.custom_headers,
        }
        if self.auth_type == "bearer" and self.auth_token:
            hdrs["Authorization"] = f"Bearer {self.auth_token}"
        if self.auth_type == "api_key" and self.api_key_header and self.api_key_value:
            hdrs[self.api_key_header] = self.api_key_value
        return hdrs

    def _build_auth(self):
        """Build httpx auth tuple for basic auth."""
        if self.auth_type == "basic" and self.auth_username and self.auth_password:
            return (self.auth_username, self.auth_password)
        return None

    def _inject_api_key_param(self, params: dict[str, Any]) -> dict[str, Any]:
        """Inject API key as a query parameter if configured."""
        if self.auth_type == "api_key" and self.api_key_query_param and self.api_key_value:
            params = dict(params)
            params[self.api_key_query_param] = self.api_key_value
        return params

    @staticmethod
    def _resolve_path(data: Any, dot_path: str) -> Any:
        """Navigate a nested dict/list using a dot-separated path.

        Examples:
            _resolve_path({"data": {"results": [1,2]}}, "data.results") -> [1, 2]
            _resolve_path({"items": [{"name": "a"}]}, "items.0.name") -> "a"
        """
        if not dot_path:
            return data

        parts = dot_path.split(".")
        current = data
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)):
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
        return current

    def _extract_text_from_value(self, value: Any) -> str:
        """Convert any value to a string for document content."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return json.dumps(value, indent=2, default=str)
        if isinstance(value, (list, tuple)):
            return "\n".join(str(v) for v in value)
        return str(value)

    def _parse_xml_response(self, text: str) -> list[dict[str, Any]]:
        """Parse an XML response into a list of dicts."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(text)

            items: list[dict[str, Any]] = []
            # Try to find repeating child elements
            children = list(root)
            if children:
                for child in children:
                    item: dict[str, Any] = {}
                    for elem in child:
                        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        item[tag] = elem.text or ""
                    if item:
                        items.append(item)

            if not items:
                # Fallback: treat root's direct children as a single item
                item = {}
                for elem in root:
                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    item[tag] = elem.text or ""
                if item:
                    items.append(item)

            return items
        except Exception as exc:
            logger.warning("XML parsing failed: %s", exc)
            return []

    async def _fetch_endpoint(self, client, endpoint: dict[str, Any]) -> list[Document]:
        """Fetch documents from a single endpoint with optional pagination."""
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET").upper()
        base_params = dict(endpoint.get("params", {}))
        body = endpoint.get("body")
        items_path = endpoint.get("items_path", "")
        content_field = endpoint.get("content_field", "")
        title_field = endpoint.get("title_field", "")
        source_field = endpoint.get("source_field", "")
        metadata_fields = endpoint.get("metadata_fields", [])
        pagination = endpoint.get("pagination", {})

        url = f"{self.base_url}{path}"
        headers = self._build_headers()
        auth = self._build_auth()

        documents: list[Document] = []
        page_count = 0
        max_ep_pages = pagination.get("max_pages", self.max_pages)

        # Pagination state
        pag_type = pagination.get("type", "none")
        offset = 0
        page_num = 1
        cursor_value: Optional[str] = None
        limit = pagination.get("limit", 100)
        limit_param = pagination.get("limit_param", "limit")
        offset_param = pagination.get("param", "offset")

        while page_count < max_ep_pages:
            params = dict(base_params)
            params = self._inject_api_key_param(params)

            # Apply pagination parameters
            if pag_type == "offset":
                params[offset_param] = offset
                params[limit_param] = limit
            elif pag_type == "page":
                params[offset_param] = page_num
                params[limit_param] = limit
            elif pag_type == "cursor" and cursor_value:
                params[pagination.get("param", "cursor")] = cursor_value
                params[limit_param] = limit
            elif pag_type == "cursor" and page_count == 0:
                params[limit_param] = limit

            # Execute request
            if method == "POST":
                resp = await client.post(url, headers=headers, auth=auth, params=params, json=body)
            else:
                resp = await client.get(url, headers=headers, auth=auth, params=params)

            resp.raise_for_status()

            # Parse response
            content_type = resp.headers.get("content-type", "")
            if "xml" in content_type:
                items = self._parse_xml_response(resp.text)
            else:
                data = resp.json()

                # Extract items from response
                if items_path:
                    items_data = self._resolve_path(data, items_path)
                else:
                    items_data = data

                if isinstance(items_data, list):
                    items = items_data
                elif isinstance(items_data, dict):
                    items = [items_data]
                else:
                    items = []

            if not items:
                break

            # Convert items to Documents
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    # Wrap non-dict items
                    item = {"value": item}

                content_val = self._resolve_path(item, content_field) if content_field else item
                content = self._extract_text_from_value(content_val)

                title_val = self._resolve_path(item, title_field) if title_field else None
                title = str(title_val) if title_val else f"{path} item {len(documents) + 1}"

                source_val = self._resolve_path(item, source_field) if source_field else None
                source = str(source_val) if source_val else f"{url}#{len(documents)}"

                meta: dict[str, Any] = {"connector": self.name, "endpoint": path}
                for mf in metadata_fields:
                    val = self._resolve_path(item, mf)
                    if val is not None:
                        meta[mf] = val

                if content.strip():
                    documents.append(Document(
                        content=content,
                        title=title,
                        source=source,
                        metadata=meta,
                    ))

            page_count += 1

            # Determine next page
            if pag_type == "offset":
                offset += limit
                if len(items) < limit:
                    break
            elif pag_type == "page":
                page_num += 1
                if len(items) < limit:
                    break
            elif pag_type == "cursor":
                cursor_path = pagination.get("cursor_path", "")
                if cursor_path and "xml" not in content_type:
                    new_cursor = self._resolve_path(data, cursor_path)
                    if new_cursor and new_cursor != cursor_value:
                        cursor_value = str(new_cursor)
                    else:
                        break
                else:
                    break
            elif pag_type == "link_header":
                link_header = resp.headers.get("Link", "")
                next_url = None
                for part in link_header.split(","):
                    if 'rel="next"' in part:
                        next_url = part.split(";")[0].strip().strip("<>")
                        break
                if next_url:
                    url = next_url
                    base_params = {}  # URL already has params
                else:
                    break
            else:
                break  # No pagination

        return documents

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull documents from all configured REST API endpoints.

        Returns:
            List of Document instances from API responses.

        Raises:
            ConnectorError: On HTTP or parsing errors.
        """
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=self.verify_ssl,
            ) as client:
                documents: list[Document] = []

                for endpoint in self.endpoints:
                    try:
                        docs = await self._fetch_endpoint(client, endpoint)
                        documents.extend(docs)
                        logger.info(
                            "REST API: fetched %d docs from %s",
                            len(docs),
                            endpoint.get("path", "/"),
                        )
                    except Exception as exc:
                        logger.warning(
                            "REST API: failed to fetch %s: %s",
                            endpoint.get("path", "/"),
                            exc,
                        )

                logger.info("REST API: total %d documents", len(documents))
                return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"REST API pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test connectivity by sending a HEAD or GET request to the base URL.

        Returns:
            True if the API responds with a non-error status.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                verify=self.verify_ssl,
            ) as client:
                headers = self._build_headers()
                auth = self._build_auth()

                # Try the first endpoint path, or just the base URL
                test_path = self.endpoints[0].get("path", "/") if self.endpoints else "/"
                url = f"{self.base_url}{test_path}"
                params = self._inject_api_key_param({})

                resp = await client.get(url, headers=headers, auth=auth, params=params)
                return resp.status_code < 500
        except Exception as exc:
            raise ConnectionTestFailedError(
                f"REST API connection test failed: {exc}"
            ) from exc
