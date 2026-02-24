"""Plugin wrapper for the MetadataEnricher transformer."""

from core.ingestion.transformers.metadata_enricher import MetadataEnricher


class MetadataEnricherPlugin:
    """Plugin interface for the metadata enricher transformer.

    Delegates to the core MetadataEnricher implementation.
    """

    def __init__(self, config=None):
        self._impl = MetadataEnricher()

    def transform(self, text, metadata=None):
        metadata = metadata or {}
        return self._impl.transform(text, metadata)
