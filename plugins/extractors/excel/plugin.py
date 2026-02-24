from core.ingestion.extractors.excel import ExcelExtractor


class ExcelExtractorPlugin:
    def __init__(self, config=None):
        self._impl = ExcelExtractor()

    def extract(self, file_path):
        return self._impl.extract(file_path)
