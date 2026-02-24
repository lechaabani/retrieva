from core.ingestion.extractors.html import HTMLExtractor


class HTMLExtractorPlugin:
    def __init__(self, config=None):
        self._impl = HTMLExtractor()

    def extract(self, file_path):
        return self._impl.extract(file_path)
