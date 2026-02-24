"""Metadata enricher transformer.

Adds computed metadata fields to documents: word count, estimated
language, and reading time.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from core.ingestion.transformers.base import BaseTransformer


# Average reading speed in words per minute
_WPM = 238

# Common words per language for lightweight detection.
# This is intentionally kept small and dependency-free.
_LANGUAGE_INDICATORS: dict[str, set[str]] = {
    "en": {"the", "and", "is", "in", "to", "of", "that", "it", "for", "was", "with"},
    "fr": {"le", "la", "les", "des", "est", "en", "que", "et", "un", "une", "dans"},
    "de": {"der", "die", "und", "ist", "von", "den", "das", "mit", "ein", "eine", "nicht"},
    "es": {"el", "la", "los", "las", "de", "en", "que", "es", "por", "con", "una"},
    "pt": {"o", "os", "as", "de", "em", "que", "uma", "para", "com", "por", "dos"},
    "it": {"il", "la", "di", "che", "del", "per", "una", "con", "sono", "gli", "dei"},
    "nl": {"de", "het", "een", "van", "en", "is", "dat", "op", "zijn", "voor", "met"},
}


class MetadataEnricher(BaseTransformer):
    """Enriches document metadata with word count, language, and reading time."""

    name = "metadata_enricher"

    def transform(
        self, text: str, metadata: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Add word_count, language, and reading_time_minutes to metadata.

        The text itself is returned unchanged.
        """
        words = text.split()
        word_count = len(words)

        metadata["word_count"] = word_count
        metadata["char_count"] = len(text)
        metadata["reading_time_minutes"] = max(1, math.ceil(word_count / _WPM))
        metadata["language"] = self._detect_language(text)

        return text, metadata

    @staticmethod
    def _detect_language(text: str) -> str:
        """Perform lightweight language detection using word frequency.

        Returns an ISO 639-1 code (e.g. ``"en"``).  Falls back to
        ``"en"`` when the language cannot be determined.
        """
        # Tokenise into lowercase words
        tokens = re.findall(r"\b[a-zA-Z\u00C0-\u024F]+\b", text.lower())
        if not tokens:
            return "unknown"

        token_set = set(tokens)
        word_freq = Counter(tokens)

        best_lang = "en"
        best_score = 0

        for lang, indicators in _LANGUAGE_INDICATORS.items():
            # Score = sum of frequencies of indicator words found in the text
            overlap = indicators & token_set
            score = sum(word_freq[w] for w in overlap)
            if score > best_score:
                best_score = score
                best_lang = lang

        return best_lang
