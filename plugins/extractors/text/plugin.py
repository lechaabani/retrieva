from core.ingestion.extractors.text import TextExtractor


class TextExtractorPlugin:
    def __init__(self, config=None):
        self._impl = TextExtractor()

    def extract(self, file_path):
        return self._impl.extract(file_path)
