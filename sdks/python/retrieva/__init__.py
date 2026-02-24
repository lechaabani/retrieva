"""Retrieva Python SDK - Official client library for the Retrieva RAG platform."""

from retrieva.async_client import AsyncRetrieva
from retrieva.client import Retrieva
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
from retrieva.types import (
    Collection,
    Document,
    IngestResponse,
    QueryResult,
    SearchHit,
    SearchResult,
    Source,
    WidgetQueryResult,
    WidgetSearchResult,
)
from retrieva.widget import AsyncWidget, Widget

__version__ = "0.1.0"

__all__ = [
    # Clients
    "Retrieva",
    "AsyncRetrieva",
    "Widget",
    "AsyncWidget",
    # Types
    "QueryResult",
    "SearchResult",
    "SearchHit",
    "Source",
    "Document",
    "Collection",
    "IngestResponse",
    "WidgetQueryResult",
    "WidgetSearchResult",
    # Errors
    "RetrievaError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "ServerError",
    "ConnectionError",
    "TimeoutError",
]
