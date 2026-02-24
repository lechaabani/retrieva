from core.connectors.url_crawler import URLCrawlerConnector


class URLCrawlerConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = URLCrawlerConnector(
            max_depth=cfg.get("max_depth", 3),
            max_pages=cfg.get("max_pages", 50),
        )

    def connect(self):
        return self._impl.connect()

    def fetch(self, url):
        return self._impl.fetch(url)
