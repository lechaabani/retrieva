"""Ingest resource for file, text, and URL ingestion."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, Optional, Union

from retrieva.types import IngestResponse


class IngestResource:
    """Handles document ingestion via the sync client.

    Provides methods to ingest files, raw text, and URLs into collections.
    """

    def __init__(self, request_fn: Callable[..., Dict[str, Any]]) -> None:
        self._request = request_fn

    def file(
        self,
        file_path: Union[str, Path],
        *,
        collection: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Upload and ingest a file into a collection.

        Args:
            file_path: Path to the file to upload.
            collection: Name or ID of the target collection.
            metadata: Optional metadata to attach to the document.

        Returns:
            An IngestResponse with the document ID and status.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        file_name = path.name

        with open(path, "rb") as f:
            files = {"file": (file_name, f, content_type)}
            form_data: Dict[str, Any] = {"collection": collection}
            if metadata is not None:
                import json

                form_data["metadata"] = json.dumps(metadata)

            data = self._request(
                "POST",
                "/api/v1/ingest",
                files=files,
                data=form_data,
            )

        return IngestResponse.from_dict(data)

    def text(
        self,
        content: str,
        *,
        title: str,
        collection: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Ingest raw text content into a collection.

        Args:
            content: The text content to ingest.
            title: Title for the document.
            collection: Name or ID of the target collection.
            metadata: Optional metadata to attach to the document.

        Returns:
            An IngestResponse with the document ID and status.
        """
        payload: Dict[str, Any] = {
            "content": content,
            "title": title,
            "collection": collection,
        }
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._request("POST", "/api/v1/ingest/text", json=payload)
        return IngestResponse.from_dict(data)

    def url(
        self,
        url: str,
        *,
        collection: str,
        crawl_depth: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Ingest content from a URL into a collection.

        Args:
            url: The URL to fetch and ingest.
            collection: Name or ID of the target collection.
            crawl_depth: How many levels of links to follow (0 = page only).
            metadata: Optional metadata to attach to the document.

        Returns:
            An IngestResponse with the document ID and status.
        """
        payload: Dict[str, Any] = {
            "url": url,
            "collection": collection,
        }
        if crawl_depth is not None:
            payload["crawl_depth"] = crawl_depth
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._request("POST", "/api/v1/ingest/url", json=payload)
        return IngestResponse.from_dict(data)


class AsyncIngestResource:
    """Handles document ingestion via the async client.

    Provides async methods to ingest files, raw text, and URLs into collections.
    """

    def __init__(
        self,
        request_fn: Callable[..., Coroutine[Any, Any, Dict[str, Any]]],
    ) -> None:
        self._request = request_fn

    async def file(
        self,
        file_path: Union[str, Path],
        *,
        collection: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Upload and ingest a file into a collection.

        Args:
            file_path: Path to the file to upload.
            collection: Name or ID of the target collection.
            metadata: Optional metadata to attach to the document.

        Returns:
            An IngestResponse with the document ID and status.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        file_name = path.name

        with open(path, "rb") as f:
            files = {"file": (file_name, f, content_type)}
            form_data: Dict[str, Any] = {"collection": collection}
            if metadata is not None:
                import json

                form_data["metadata"] = json.dumps(metadata)

            data = await self._request(
                "POST",
                "/api/v1/ingest",
                files=files,
                data=form_data,
            )

        return IngestResponse.from_dict(data)

    async def text(
        self,
        content: str,
        *,
        title: str,
        collection: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Ingest raw text content into a collection.

        Args:
            content: The text content to ingest.
            title: Title for the document.
            collection: Name or ID of the target collection.
            metadata: Optional metadata to attach to the document.

        Returns:
            An IngestResponse with the document ID and status.
        """
        payload: Dict[str, Any] = {
            "content": content,
            "title": title,
            "collection": collection,
        }
        if metadata is not None:
            payload["metadata"] = metadata

        data = await self._request("POST", "/api/v1/ingest/text", json=payload)
        return IngestResponse.from_dict(data)

    async def url(
        self,
        url: str,
        *,
        collection: str,
        crawl_depth: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResponse:
        """Ingest content from a URL into a collection.

        Args:
            url: The URL to fetch and ingest.
            collection: Name or ID of the target collection.
            crawl_depth: How many levels of links to follow (0 = page only).
            metadata: Optional metadata to attach to the document.

        Returns:
            An IngestResponse with the document ID and status.
        """
        payload: Dict[str, Any] = {
            "url": url,
            "collection": collection,
        }
        if crawl_depth is not None:
            payload["crawl_depth"] = crawl_depth
        if metadata is not None:
            payload["metadata"] = metadata

        data = await self._request("POST", "/api/v1/ingest/url", json=payload)
        return IngestResponse.from_dict(data)
