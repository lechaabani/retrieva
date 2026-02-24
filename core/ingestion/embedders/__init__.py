"""Embedding providers for converting text to vector representations."""

from __future__ import annotations

from typing import Any

from core.ingestion.embedders.base import BaseEmbedder
from core.ingestion.embedders.cohere import CohereEmbedder
from core.ingestion.embedders.local import LocalEmbedder
from core.ingestion.embedders.openai import OpenAIEmbedder

__all__ = [
    "BaseEmbedder",
    "OpenAIEmbedder",
    "LocalEmbedder",
    "CohereEmbedder",
    "get_embedder",
]

_EMBEDDER_MAP: dict[str, type[BaseEmbedder]] = {
    "openai": OpenAIEmbedder,
    "local": LocalEmbedder,
    "cohere": CohereEmbedder,
}


def get_embedder(
    provider: str = "openai",
    model: str | None = None,
    **kwargs: Any,
) -> BaseEmbedder:
    """Return an embedder instance, trying the plugin manager first then falling back.

    Args:
        provider: Embedding provider name (openai, local, cohere).
        model: Model name/identifier.

    Returns:
        A configured BaseEmbedder instance.
    """
    # Try plugin manager first
    try:
        from core.plugin_system.manager import get_plugin_manager

        pm = get_plugin_manager()
        config: dict[str, Any] = {**kwargs}
        if model:
            config["model"] = model
        plugin = pm.get_plugin("embedder", provider, config=config)
        return plugin
    except Exception:
        pass

    # Fallback to built-in embedders
    cls = _EMBEDDER_MAP.get(provider)
    if cls is None:
        raise ValueError(f"Unknown embedding provider: {provider}")

    init_kwargs: dict[str, Any] = {**kwargs}
    if model:
        init_kwargs["model"] = model
    return cls(**init_kwargs)
