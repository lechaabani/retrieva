"""Search resource mixin for semantic search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from retrieva.types import SearchResult

if TYPE_CHECKING:
    from retrieva.async_client import AsyncRetrieva
    from retrieva.client import Retrieva


class SearchMixin:
    """Mixin that adds the search() method to the sync client."""

    def search(
        self: Retrieva,
        query: str,
        *,
        collection_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> SearchResult:
        """Perform a semantic search across documents.

        Args:
            query: The search query string.
            collection_id: Restrict search to a specific collection.
            top_k: Maximum number of results to return.

        Returns:
            A SearchResult containing matching document chunks with scores.
        """
        payload: dict = {"query": query}
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if top_k is not None:
            payload["top_k"] = top_k

        data = self._request("POST", "/api/v1/search", json=payload)
        return SearchResult.from_dict(data)


class AsyncSearchMixin:
    """Mixin that adds the search() method to the async client."""

    async def search(
        self: AsyncRetrieva,
        query: str,
        *,
        collection_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> SearchResult:
        """Perform a semantic search across documents.

        Args:
            query: The search query string.
            collection_id: Restrict search to a specific collection.
            top_k: Maximum number of results to return.

        Returns:
            A SearchResult containing matching document chunks with scores.
        """
        payload: dict = {"query": query}
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if top_k is not None:
            payload["top_k"] = top_k

        data = await self._request("POST", "/api/v1/search", json=payload)
        return SearchResult.from_dict(data)
