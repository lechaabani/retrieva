"""Plugin wrapper for the HTMLCleaner transformer."""

from core.ingestion.transformers.html_cleaner import HTMLCleaner


class HTMLCleanerPlugin:
    """Plugin interface for the HTML cleaner transformer.

    Delegates to the core HTMLCleaner implementation.
    """

    def __init__(self, config=None):
        self._impl = HTMLCleaner()

    def transform(self, text, metadata=None):
        metadata = metadata or {}
        return self._impl.transform(text, metadata)
