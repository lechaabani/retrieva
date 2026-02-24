"""Protocol definitions for all Retrieva plugin types.

Plugins satisfy these contracts via structural subtyping (duck typing).
No inheritance required — just implement the methods.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ChunkerPlugin(Protocol):
    """Split text into chunks for embedding and retrieval."""

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list: ...


@runtime_checkable
class EmbedderPlugin(Protocol):
    """Generate vector embeddings from text."""

    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class ConnectorPlugin(Protocol):
    """Pull documents from an external data source."""

    name: str

    async def pull(self) -> list: ...

    async def test_connection(self) -> bool: ...


@runtime_checkable
class ExtractorPlugin(Protocol):
    """Extract text content from a file or bytes."""

    supported_extensions: list[str]

    async def extract(self, source: Any) -> Any: ...


@runtime_checkable
class RetrieverPlugin(Protocol):
    """Search a collection and return ranked chunks."""

    async def search(
        self,
        query: str,
        collection_id: str,
        top_k: int = 10,
        **kwargs: Any,
    ) -> list[dict[str, Any]]: ...


@runtime_checkable
class GeneratorPlugin(Protocol):
    """Call an LLM and return generated text."""

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> tuple[str, int]: ...


@runtime_checkable
class GuardrailPlugin(Protocol):
    """Validate generated answers for hallucinations and relevance."""

    def check(
        self,
        answer: str,
        context: str,
        query: str,
    ) -> dict[str, Any]: ...


@runtime_checkable
class TemplatePlugin(Protocol):
    """Embeddable UI template (chatbot widget, search bar, etc.)."""

    def get_assets(self) -> dict[str, str]: ...

    def render(self, config: dict[str, Any]) -> str: ...


# Map plugin type names to their Protocol classes.
PLUGIN_TYPE_PROTOCOLS: dict[str, type] = {
    "chunker": ChunkerPlugin,
    "embedder": EmbedderPlugin,
    "connector": ConnectorPlugin,
    "extractor": ExtractorPlugin,
    "retriever": RetrieverPlugin,
    "generator": GeneratorPlugin,
    "guardrail": GuardrailPlugin,
    "template": TemplatePlugin,
}
