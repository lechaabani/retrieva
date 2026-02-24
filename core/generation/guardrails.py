"""Guardrails for generation quality control.

Provides basic heuristic checks for hallucination detection and relevance
scoring without requiring additional ML models.
"""

from __future__ import annotations

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


class Guardrails:
    """Heuristic guardrails for validating generated answers.

    Uses keyword overlap and simple statistical methods rather than
    external models, making these checks fast and dependency-free.
    """

    def __init__(
        self,
        hallucination_threshold: float = 0.5,
        relevance_threshold: float = 0.2,
    ) -> None:
        """
        Args:
            hallucination_threshold: Minimum confidence score to accept an answer.
            relevance_threshold: Minimum overlap ratio for relevance check.
        """
        self.hallucination_threshold = hallucination_threshold
        self.relevance_threshold = relevance_threshold

    def check_hallucination(self, answer: str, context: str) -> float:
        """Estimate confidence that the answer is grounded in the context.

        Uses content-word overlap between the answer and context as a
        proxy for groundedness. Higher scores indicate better grounding.

        Args:
            answer: The generated answer text.
            context: The context text that was provided to the LLM.

        Returns:
            A confidence score in [0.0, 1.0]. Values below
            ``hallucination_threshold`` suggest potential hallucination.
        """
        if not answer or not context:
            return 0.0

        answer_tokens = self._extract_content_words(answer)
        context_tokens = self._extract_content_words(context)

        if not answer_tokens:
            return 0.0

        context_set = set(context_tokens)
        overlap_count = sum(1 for t in answer_tokens if t in context_set)
        coverage = overlap_count / len(answer_tokens)

        # Boost score if answer cites sources (e.g. "[Source 1]")
        citation_pattern = re.compile(r"\[Source\s+\d+\]", re.IGNORECASE)
        citations = citation_pattern.findall(answer)
        citation_bonus = min(len(citations) * 0.05, 0.15)

        confidence = min(coverage + citation_bonus, 1.0)

        logger.debug(
            "Hallucination check: coverage=%.2f, citations=%d, confidence=%.2f",
            coverage,
            len(citations),
            confidence,
        )
        return confidence

    def check(
        self, answer: str, context: str, query: str
    ) -> dict:
        """Run all guardrail checks and return a unified result.

        This is the main entry point used by the plugin system's
        ``GuardrailPlugin`` protocol.

        Args:
            answer: The generated answer text.
            context: The context that was provided to the LLM.
            query: The original user question.

        Returns:
            A dict with keys: ``passed`` (bool), ``confidence`` (float),
            ``relevant`` (bool), ``safe`` (bool), ``issues`` (list[str]).
        """
        issues: list[str] = []

        confidence = self.check_hallucination(answer, context)
        relevant = self.check_relevance(answer, query)
        safe = self.check_content_safety(answer)

        if confidence < self.hallucination_threshold:
            issues.append(
                f"Low groundedness confidence ({confidence:.2f} < {self.hallucination_threshold})"
            )
        if not relevant:
            issues.append("Answer may not be relevant to the question")
        if not safe:
            issues.append("Answer contains potentially unsafe content")

        passed = confidence >= self.hallucination_threshold and relevant and safe
        return {
            "passed": passed,
            "confidence": round(confidence, 3),
            "relevant": relevant,
            "safe": safe,
            "issues": issues,
        }

    def check_content_safety(self, answer: str) -> bool:
        """Basic content safety check for obviously problematic outputs.

        Checks for common patterns that indicate the LLM may have gone
        off-track (e.g. role-play leaking, instruction echoing).

        Args:
            answer: The generated answer text.

        Returns:
            True if the answer passes basic safety checks.
        """
        if not answer:
            return True

        lower = answer.lower()

        # Detect instruction leaking / role confusion
        leak_patterns = [
            "as an ai language model",
            "i cannot help with",
            "i'm sorry, but i cannot",
            "my instructions say",
            "system prompt",
        ]
        for pattern in leak_patterns:
            if pattern in lower:
                logger.warning("Content safety: instruction leak detected")
                return False

        return True

    def check_relevance(self, answer: str, question: str) -> bool:
        """Check whether the answer is relevant to the question.

        Uses keyword overlap between the question and answer as a
        basic relevance signal.

        Args:
            answer: The generated answer text.
            question: The original user question.

        Returns:
            True if the answer appears relevant to the question.
        """
        if not answer or not question:
            return False

        question_tokens = set(self._extract_content_words(question))
        answer_tokens = set(self._extract_content_words(answer))

        if not question_tokens:
            return True  # Cannot assess, assume relevant

        overlap = question_tokens & answer_tokens
        ratio = len(overlap) / len(question_tokens)

        is_relevant = ratio >= self.relevance_threshold

        logger.debug(
            "Relevance check: overlap=%d/%d (%.2f), relevant=%s",
            len(overlap),
            len(question_tokens),
            ratio,
            is_relevant,
        )
        return is_relevant

    @staticmethod
    def _extract_content_words(text: str) -> list[str]:
        """Extract lowercased content words, filtering out stop words and short tokens."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "about", "between",
            "through", "during", "before", "after", "above", "below", "and", "but",
            "or", "nor", "not", "so", "yet", "both", "either", "neither", "each",
            "every", "all", "any", "few", "more", "most", "other", "some", "such",
            "no", "only", "own", "same", "than", "too", "very", "just", "because",
            "if", "when", "where", "how", "what", "which", "who", "whom", "this",
            "that", "these", "those", "it", "its", "i", "me", "my", "we", "our",
            "you", "your", "he", "him", "his", "she", "her", "they", "them", "their",
        }
        words = re.findall(r"\b[a-z]+\b", text.lower())
        return [w for w in words if len(w) > 2 and w not in stop_words]
