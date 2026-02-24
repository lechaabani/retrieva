"""Custom exception hierarchy for the Retrieva platform."""


class RetrievaError(Exception):
    """Base exception for all Retrieva errors."""


# ── Ingestion ──────────────────────────────────────────────────────────────────

class IngestionError(RetrievaError):
    """Raised when the ingestion pipeline encounters an unrecoverable error."""


class ExtractionError(IngestionError):
    """Raised when content extraction from a source fails."""


class ChunkingError(IngestionError):
    """Raised when text chunking fails."""


class EmbeddingError(IngestionError):
    """Raised when computing embeddings fails."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when a file type has no registered extractor."""


# ── Retrieval ──────────────────────────────────────────────────────────────────

class RetrievalError(RetrievaError):
    """Raised when the retrieval engine encounters an error."""


class CollectionNotFoundError(RetrievalError):
    """Raised when a requested vector collection does not exist."""


# ── Generation ─────────────────────────────────────────────────────────────────

class GenerationError(RetrievaError):
    """Raised when the LLM generation step fails."""


class GuardrailViolation(GenerationError):
    """Raised when a guardrail check fails and the answer is rejected."""


# ── Connectors ─────────────────────────────────────────────────────────────────

class ConnectorError(RetrievaError):
    """Raised when a data connector encounters an error."""


class ConnectionTestFailedError(ConnectorError):
    """Raised when a connector's test_connection check fails."""


# ── Vector Store ───────────────────────────────────────────────────────────────

class VectorStoreError(RetrievaError):
    """Raised when vector store operations fail."""


# ── Configuration ──────────────────────────────────────────────────────────────

class ConfigurationError(RetrievaError):
    """Raised when configuration is invalid or missing."""


# ── Plugins ───────────────────────────────────────────────────────────────────

class PluginError(RetrievaError):
    """Base exception for plugin system errors."""


class PluginLoadError(PluginError):
    """Raised when a plugin cannot be loaded or instantiated."""


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin is not installed or is disabled."""
