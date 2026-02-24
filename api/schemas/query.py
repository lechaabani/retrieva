"""Schemas for RAG query and semantic search endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QueryOptions(BaseModel):
    """Optional parameters for tuning RAG query behaviour."""

    top_k: int = Field(default=10, ge=1, le=100, description="Number of chunks to retrieve")
    include_sources: bool = Field(default=True, description="Include source references in response")
    language: str = Field(default="en", max_length=10, description="Response language code")
    max_tokens: int = Field(default=500, ge=50, le=4096, description="Maximum tokens in generated answer")


class QueryRequest(BaseModel):
    """Payload for a full RAG query (retrieval + generation)."""

    question: str = Field(..., min_length=1, max_length=2000, description="The question to answer")
    collection: str = Field(..., min_length=1, max_length=255, description="Target collection name")
    options: Optional[QueryOptions] = Field(default=None, description="Query tuning options")

    model_config = {"json_schema_extra": {"examples": [{"question": "What is our refund policy?", "collection": "knowledge-base"}]}}


class Source(BaseModel):
    """A source reference used to generate the answer."""

    document_id: str = ""
    chunk_id: str = ""
    title: str = ""
    content: str = ""
    score: float = Field(default=0.0, ge=0.0)
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """Response from a RAG query."""

    answer: str
    sources: list[Source] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    tokens_used: int = Field(ge=0)


class SearchResult(BaseModel):
    """A single semantic search result."""

    chunk_id: str = ""
    document_id: str = ""
    title: str = ""
    content: str = ""
    score: float = Field(default=0.0, ge=0.0)
    metadata: dict = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Payload for a semantic search (retrieval only, no generation)."""

    query: str = Field(..., min_length=1, max_length=2000, description="Search query")
    collection: str = Field(..., min_length=1, max_length=255, description="Target collection name")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    filters: Optional[dict] = Field(default=None, description="Metadata filters for narrowing results")


class SearchResponse(BaseModel):
    """Response from a semantic search."""

    results: list[SearchResult] = Field(default_factory=list)
    total: int = Field(ge=0)


# ---------------------------------------------------------------------------
# Debug pipeline schemas
# ---------------------------------------------------------------------------

class DebugChunk(BaseModel):
    """A chunk reference returned within a debug step."""

    content: str = ""
    score: float = Field(default=0.0, ge=0.0)
    doc_id: str = ""


class DebugStep(BaseModel):
    """One step of the RAG pipeline with timing and intermediate data."""

    name: str = Field(..., description="Machine-readable step identifier (e.g. 'embedding', 'retrieval')")
    label: str = Field(..., description="Human-readable step label")
    duration_ms: int = Field(ge=0, description="Wall-clock time for this step in milliseconds")
    details: dict = Field(default_factory=dict, description="Step-specific metadata")
    chunks: Optional[list[DebugChunk]] = Field(default=None, description="Intermediate chunk results (if applicable)")


class DebugQueryResponse(BaseModel):
    """Response from the debug RAG pipeline endpoint."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    total_latency_ms: int = Field(ge=0)
    steps: list[DebugStep] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
