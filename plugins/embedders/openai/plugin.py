from core.ingestion.embedders.openai import OpenAIEmbedder


class OpenAIEmbedderPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = OpenAIEmbedder(
            model=cfg.get("model", "text-embedding-3-small"),
            dimensions=cfg.get("dimensions", 1536),
        )

    def embed(self, texts):
        return self._impl.embed(texts)
