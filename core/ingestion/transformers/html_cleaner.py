"""HTML cleaner transformer.

Strips HTML tags, decodes entities, and normalises whitespace so that
downstream chunkers receive clean plain text.
"""

from __future__ import annotations

import html
import re
from typing import Any

from core.ingestion.transformers.base import BaseTransformer


class HTMLCleaner(BaseTransformer):
    """Strips HTML markup and normalises whitespace."""

    name = "html_cleaner"

    # Tags whose content should be removed entirely (not just the tags).
    _REMOVE_CONTENT_TAGS = re.compile(
        r"<(script|style|head|noscript|iframe)[^>]*>.*?</\1>",
        re.IGNORECASE | re.DOTALL,
    )

    # Any remaining HTML tags.
    _TAG_RE = re.compile(r"<[^>]+>")

    # HTML comments.
    _COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

    def transform(
        self, text: str, metadata: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Remove HTML tags and normalise whitespace.

        If the text does not appear to contain HTML, it is returned
        unchanged apart from whitespace normalisation.
        """
        # Quick check: if there's no '<' the text is probably not HTML.
        if "<" not in text:
            return text, metadata

        cleaned = text

        # Remove comments first
        cleaned = self._COMMENT_RE.sub("", cleaned)

        # Remove script/style/head blocks including their content
        cleaned = self._REMOVE_CONTENT_TAGS.sub("", cleaned)

        # Replace block-level tags with newlines to preserve paragraph structure
        block_tags = re.compile(
            r"</?(?:p|div|br|hr|h[1-6]|li|tr|blockquote|pre|section|article|header|footer|nav|aside|main|figure|figcaption|details|summary|table|thead|tbody|tfoot|ul|ol|dl|dt|dd)[^>]*>",
            re.IGNORECASE,
        )
        cleaned = block_tags.sub("\n", cleaned)

        # Strip all remaining tags
        cleaned = self._TAG_RE.sub("", cleaned)

        # Decode HTML entities
        cleaned = html.unescape(cleaned)

        # Normalise whitespace
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = cleaned.strip()

        metadata["html_cleaned"] = True

        return cleaned, metadata
