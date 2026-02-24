from core.retrieval.engine import RetrievalEngine


class HybridRetrieverPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = RetrievalEngine(
            strategy="hybrid",
            **{k: v for k, v in cfg.items() if k != "strategy"},
        )

    def search(self, query, top_k=None):
        kwargs = {}
        if top_k is not None:
            kwargs["top_k"] = top_k
        return self._impl.search(query, **kwargs)
