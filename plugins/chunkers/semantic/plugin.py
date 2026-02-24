from core.ingestion.chunkers.semantic import SemanticChunker


class SemanticChunkerPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = SemanticChunker(
            max_chunk_tokens=cfg.get("max_chunk_tokens", 512),
            min_chunk_tokens=cfg.get("min_chunk_tokens", 50),
        )

    def chunk(self, text):
        return self._impl.chunk(text)
