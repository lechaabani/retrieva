from core.ingestion.chunkers.document import DocumentChunker


class DocumentChunkerPlugin:
    def __init__(self, config=None):
        self._impl = DocumentChunker()

    def chunk(self, text):
        return self._impl.chunk(text)
