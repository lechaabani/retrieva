"""Query resource mixin for RAG queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from retrieva.types import QueryResult

if TYPE_CHECKING:
    from retrieva.async_client import AsyncRetrieva
    from retrieva.client import Retrieva


class QueryMixin:
    """Mixin that adds the query() method to the sync client."""

    def query(
        self: Retrieva,
        question: str,
        *,
        collection_id: Optional[str] = None,
        top_k: Optional[int] = None,
        include_sources: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> QueryResult:
        """Perform a RAG query and get an AI-generated answer with sources.

        Args:
            question: The question to ask.
            collection_id: Restrict the query to a specific collection.
            top_k: Maximum number of source chunks to retrieve.
            include_sources: Whether to include source documents in the response.
            language: Language code for the response (e.g. "en", "fr").

        Returns:
            A QueryResult containing the answer, sources, and confidence score.
        """
        payload: dict = {"question": question}
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if top_k is not None:
            payload["top_k"] = top_k
        if include_sources is not None:
            payload["include_sources"] = include_sources
        if language is not None:
            payload["language"] = language

        data = self._request("POST", "/api/v1/query", json=payload)
        return QueryResult.from_dict(data)


class AsyncQueryMixin:
    """Mixin that adds the query() method to the async client."""

    async def query(
        self: AsyncRetrieva,
        question: str,
        *,
        collection_id: Optional[str] = None,
        top_k: Optional[int] = None,
        include_sources: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> QueryResult:
        """Perform a RAG query and get an AI-generated answer with sources.

        Args:
            question: The question to ask.
            collection_id: Restrict the query to a specific collection.
            top_k: Maximum number of source chunks to retrieve.
            include_sources: Whether to include source documents in the response.
            language: Language code for the response (e.g. "en", "fr").

        Returns:
            A QueryResult containing the answer, sources, and confidence score.
        """
        payload: dict = {"question": question}
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if top_k is not None:
            payload["top_k"] = top_k
        if include_sources is not None:
            payload["include_sources"] = include_sources
        if language is not None:
            payload["language"] = language

        data = await self._request("POST", "/api/v1/query", json=payload)
        return QueryResult.from_dict(data)
