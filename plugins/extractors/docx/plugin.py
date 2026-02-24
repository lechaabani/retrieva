from core.ingestion.extractors.docx import DocxExtractor


class DocxExtractorPlugin:
    def __init__(self, config=None):
        self._impl = DocxExtractor()

    def extract(self, file_path):
        return self._impl.extract(file_path)
