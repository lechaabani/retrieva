from core.ingestion.chunkers.fixed import FixedChunker


class FixedChunkerPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = FixedChunker(
            chunk_size=cfg.get("chunk_size", 512),
            chunk_overlap=cfg.get("chunk_overlap", 64),
        )

    def chunk(self, text):
        return self._impl.chunk(text)
