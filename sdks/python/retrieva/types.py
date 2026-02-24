"""Typed dataclasses for Retrieva SDK responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Source:
    """A source reference returned alongside a query answer."""

    content: str = ""
    title: str = ""
    source: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Source:
        return cls(
            content=data.get("content", ""),
            title=data.get("title", ""),
            source=data.get("source", ""),
            score=data.get("score", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class QueryResult:
    """Response from a RAG query."""

    answer: str = ""
    sources: List[Source] = field(default_factory=list)
    confidence: float = 0.0
    query: str = ""
    collection_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QueryResult:
        sources = [Source.from_dict(s) for s in data.get("sources", [])]
        return cls(
            answer=data.get("answer", ""),
            sources=sources,
            confidence=data.get("confidence", 0.0),
            query=data.get("query", ""),
            collection_id=data.get("collection_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchHit:
    """A single search result."""

    content: str = ""
    title: str = ""
    source: str = ""
    score: float = 0.0
    document_id: Optional[str] = None
    collection_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SearchHit:
        return cls(
            content=data.get("content", ""),
            title=data.get("title", ""),
            source=data.get("source", ""),
            score=data.get("score", 0.0),
            document_id=data.get("document_id"),
            collection_id=data.get("collection_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchResult:
    """Response from a semantic search."""

    results: List[SearchHit] = field(default_factory=list)
    query: str = ""
    total: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SearchResult:
        results = [SearchHit.from_dict(h) for h in data.get("results", [])]
        return cls(
            results=results,
            query=data.get("query", ""),
            total=data.get("total", len(results)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Document:
    """A document stored in a collection."""

    id: str = ""
    title: str = ""
    content: str = ""
    source: str = ""
    collection_id: str = ""
    status: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Document:
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            collection_id=data.get("collection_id", ""),
            status=data.get("status", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Collection:
    """A document collection."""

    id: str = ""
    name: str = ""
    description: str = ""
    document_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Collection:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            document_count=data.get("document_count", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class IngestResponse:
    """Response from an ingestion request."""

    document_id: str = ""
    status: str = ""
    message: str = ""
    collection_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IngestResponse:
        return cls(
            document_id=data.get("document_id", ""),
            status=data.get("status", ""),
            message=data.get("message", ""),
            collection_id=data.get("collection_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WidgetQueryResult:
    """Response from a widget query."""

    answer: str = ""
    sources: List[Source] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WidgetQueryResult:
        sources = [Source.from_dict(s) for s in data.get("sources", [])]
        return cls(
            answer=data.get("answer", ""),
            sources=sources,
            confidence=data.get("confidence", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class WidgetSearchResult:
    """Response from a widget search."""

    results: List[SearchHit] = field(default_factory=list)
    query: str = ""
    total: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WidgetSearchResult:
        results = [SearchHit.from_dict(h) for h in data.get("results", [])]
        return cls(
            results=results,
            query=data.get("query", ""),
            total=data.get("total", len(results)),
            metadata=data.get("metadata", {}),
        )
