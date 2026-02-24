"""Synchronous Retrieva client."""

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
from retrieva.resources.collections import CollectionsResource
from retrieva.resources.ingest import IngestResource
from retrieva.resources.query import QueryMixin
from retrieva.resources.search import SearchMixin

_DEFAULT_BASE_URL = "https://api.retrieva.io"
_DEFAULT_TIMEOUT = 30.0
_SDK_VERSION = "0.1.0"


class Retrieva(QueryMixin, SearchMixin):
    """Synchronous client for the Retrieva RAG API.

    Usage::

        from retrieva import Retrieva

        rag = Retrieva(api_key="rtv_xxx", base_url="https://api.example.com")
        result = rag.query("How to configure X?", collection_id="uuid")
        print(result.answer)

    Args:
        api_key: Your Retrieva API key (e.g. ``rtv_xxx``).
        base_url: Base URL of the Retrieva API. Defaults to ``https://api.retrieva.io``.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Number of automatic retries on transient failures. Defaults to 2.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = 2,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

        transport = httpx.HTTPTransport(retries=max_retries)
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": f"retrieva-python/{_SDK_VERSION}",
                "Accept": "application/json",
            },
            timeout=timeout,
            transport=transport,
        )

        # Sub-resources
        self.ingest = IngestResource(self._request)
        self.collections = CollectionsResource(self._request)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Send an HTTP request and return the parsed JSON response.

        Raises appropriate SDK exceptions based on the HTTP status code.
        """
        try:
            response = self._client.request(
                method,
                path,
                json=json,
                data=data,
                files=files,
                params=params,
            )
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Request to {path} timed out") from exc

        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response) -> Any:
        """Parse the response, raising typed exceptions on error."""
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

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Retrieva:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Retrieva(base_url={self._base_url!r})"
