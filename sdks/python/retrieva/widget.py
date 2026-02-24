"""Widget clients for public-facing widget queries and search."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from retrieva.errors import (
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    RetrievaError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from retrieva.types import SearchHit, WidgetQueryResult, WidgetSearchResult

_DEFAULT_BASE_URL = "https://api.retrieva.io"
_DEFAULT_TIMEOUT = 30.0
_SDK_VERSION = "0.1.0"


def _handle_response(response: httpx.Response) -> Any:
    """Shared response handler for widget clients."""
    if response.status_code == 204:
        return {}

    try:
        body = response.json()
    except Exception:
        body = {}

    if response.is_success:
        return body

    message = body.get("detail", body.get("message", response.text))

    if response.status_code in (401, 403):
        raise AuthenticationError(
            message=message, status_code=response.status_code, body=body
        )
    if response.status_code == 404:
        raise NotFoundError(
            message=message, status_code=response.status_code, body=body
        )
    if response.status_code == 422:
        raise ValidationError(
            message=message, status_code=response.status_code, body=body
        )
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        raise RateLimitError(
            message=message,
            status_code=response.status_code,
            body=body,
            retry_after=float(retry_after) if retry_after else None,
        )
    if response.status_code >= 500:
        raise ServerError(
            message=message, status_code=response.status_code, body=body
        )

    raise RetrievaError(
        message=message, status_code=response.status_code, body=body
    )


class Widget:
    """Synchronous client for the public Retrieva widget API.

    Usage::

        from retrieva import Widget

        widget = Widget(api_key="rtv_pub_xxx", widget_id="uuid")
        answer = widget.query("How does this work?")
        print(answer.answer)

    Args:
        api_key: Your public widget API key.
        widget_id: The widget UUID.
        base_url: Base URL of the Retrieva API.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        *,
        widget_id: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not widget_id:
            raise ValueError("widget_id is required")

        self._api_key = api_key
        self._widget_id = widget_id
        self._base_url = base_url.rstrip("/")

        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": f"retrieva-python-widget/{_SDK_VERSION}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def query(self, question: str) -> WidgetQueryResult:
        """Send a query through the widget endpoint.

        Args:
            question: The question to ask.

        Returns:
            A WidgetQueryResult with the answer and sources.
        """
        payload = {"question": question, "widget_id": self._widget_id}
        try:
            response = self._client.post("/widget/query", json=payload)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Widget query timed out") from exc

        data = _handle_response(response)
        return WidgetQueryResult.from_dict(data)

    def search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
    ) -> WidgetSearchResult:
        """Perform a semantic search through the widget endpoint.

        Args:
            query: The search query.
            top_k: Maximum number of results.

        Returns:
            A WidgetSearchResult with matching hits.
        """
        payload: Dict[str, Any] = {
            "query": query,
            "widget_id": self._widget_id,
        }
        if top_k is not None:
            payload["top_k"] = top_k

        try:
            response = self._client.post("/widget/search", json=payload)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Widget search timed out") from exc

        data = _handle_response(response)
        return WidgetSearchResult.from_dict(data)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Widget:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Widget(widget_id={self._widget_id!r}, base_url={self._base_url!r})"


class AsyncWidget:
    """Asynchronous client for the public Retrieva widget API.

    Usage::

        import asyncio
        from retrieva import AsyncWidget

        async def main():
            async with AsyncWidget(api_key="rtv_pub_xxx", widget_id="uuid") as widget:
                answer = await widget.query("How does this work?")
                print(answer.answer)

        asyncio.run(main())

    Args:
        api_key: Your public widget API key.
        widget_id: The widget UUID.
        base_url: Base URL of the Retrieva API.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        *,
        widget_id: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not widget_id:
            raise ValueError("widget_id is required")

        self._api_key = api_key
        self._widget_id = widget_id
        self._base_url = base_url.rstrip("/")

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": f"retrieva-python-widget/{_SDK_VERSION}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def query(self, question: str) -> WidgetQueryResult:
        """Send a query through the widget endpoint.

        Args:
            question: The question to ask.

        Returns:
            A WidgetQueryResult with the answer and sources.
        """
        payload = {"question": question, "widget_id": self._widget_id}
        try:
            response = await self._client.post("/widget/query", json=payload)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Widget query timed out") from exc

        data = _handle_response(response)
        return WidgetQueryResult.from_dict(data)

    async def search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
    ) -> WidgetSearchResult:
        """Perform a semantic search through the widget endpoint.

        Args:
            query: The search query.
            top_k: Maximum number of results.

        Returns:
            A WidgetSearchResult with matching hits.
        """
        payload: Dict[str, Any] = {
            "query": query,
            "widget_id": self._widget_id,
        }
        if top_k is not None:
            payload["top_k"] = top_k

        try:
            response = await self._client.post("/widget/search", json=payload)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Widget search timed out") from exc

        data = _handle_response(response)
        return WidgetSearchResult.from_dict(data)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncWidget:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"AsyncWidget(widget_id={self._widget_id!r}, base_url={self._base_url!r})"
