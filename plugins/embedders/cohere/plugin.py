from core.ingestion.embedders.cohere import CohereEmbedder


class CohereEmbedderPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = CohereEmbedder(
            model=cfg.get("model", "embed-english-v3.0"),
        )

    def embed(self, texts):
        return self._impl.embed(texts)
