from core.ingestion.embedders.local import LocalEmbedder


class LocalEmbedderPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = LocalEmbedder(
            model=cfg.get("model", "all-MiniLM-L6-v2"),
            device=cfg.get("device", "cpu"),
        )

    def embed(self, texts):
        return self._impl.embed(texts)
