"""Transform/enrichment pipeline phase for ingestion.

Transformers run between the clean and chunk stages, modifying text
and metadata before chunking takes place.
"""

from core.ingestion.transformers.base import BaseTransformer
from core.ingestion.transformers.metadata_enricher import MetadataEnricher
from core.ingestion.transformers.html_cleaner import HTMLCleaner
from core.ingestion.transformers.deduplicator import Deduplicator

__all__ = [
    "BaseTransformer",
    "MetadataEnricher",
    "HTMLCleaner",
    "Deduplicator",
]
