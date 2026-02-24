from core.ingestion.extractors.pdf import PDFExtractor


class PDFExtractorPlugin:
    def __init__(self, config=None):
        self._impl = PDFExtractor()

    def extract(self, file_path):
        return self._impl.extract(file_path)
