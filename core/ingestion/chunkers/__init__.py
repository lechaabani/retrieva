"""Text chunking strategies for the ingestion pipeline."""

from __future__ import annotations

from typing import Any

from core.ingestion.chunkers.base import BaseChunker, Chunk
from core.ingestion.chunkers.document import DocumentChunker
from core.ingestion.chunkers.fixed import FixedChunker
from core.ingestion.chunkers.semantic import SemanticChunker

__all__ = [
    "BaseChunker",
    "Chunk",
    "FixedChunker",
    "SemanticChunker",
    "DocumentChunker",
    "get_chunker",
]

_CHUNKER_MAP: dict[str, type[BaseChunker]] = {
    "fixed": FixedChunker,
    "semantic": SemanticChunker,
    "document": DocumentChunker,
}


def get_chunker(
    strategy: str = "semantic",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    **kwargs: Any,
) -> BaseChunker:
    """Return a chunker instance, trying the plugin manager first then falling back.

    Args:
        strategy: Chunking strategy name (fixed, semantic, document).
        chunk_size: Target chunk size in tokens.
        chunk_overlap: Overlap between chunks (fixed strategy).

    Returns:
        A configured BaseChunker instance.
    """
    # Try plugin manager first
    try:
        from core.plugin_system.manager import get_plugin_manager

        pm = get_plugin_manager()
        plugin = pm.get_plugin("chunker", strategy, config={
            "chunk_size": chunk_size,
            "max_chunk_tokens": chunk_size,
            "chunk_overlap": chunk_overlap,
            **kwargs,
        })
        return plugin
    except Exception:
        pass

    # Fallback to built-in chunkers
    cls = _CHUNKER_MAP.get(strategy)
    if cls is None:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

    if strategy == "fixed":
        return FixedChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif strategy == "semantic":
        return SemanticChunker(max_chunk_tokens=chunk_size)
    else:
        return DocumentChunker()
