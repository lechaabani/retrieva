"""Generation engine: context assembly, prompt building, LLM calling, and citation extraction."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from core.exceptions import GenerationError
from core.generation.guardrails import Guardrails
from core.generation.prompts import build_prompt_from_template, format_context
from core.retrieval.engine import ScoredChunk

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Output of a generation call."""

    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    tokens_used: int = 0
    model: str = ""
    is_relevant: bool = True


class GenerationEngine:
    """Orchestrates context assembly, prompt building, and LLM generation.

    Supports OpenAI, Anthropic, and Ollama as LLM providers.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_context_chunks: int = 8,
        persona: str = "You are a helpful assistant that answers questions based on the provided context.",
        api_key: Optional[str] = None,
        enable_guardrails: bool = True,
        hallucination_threshold: float = 0.5,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Args:
            provider: LLM provider ("openai", "anthropic", "ollama").
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.
            max_context_chunks: Maximum chunks to include in context.
            persona: System persona for prompt construction.
            api_key: API key (falls back to env var).
            enable_guardrails: Whether to run guardrail checks.
            hallucination_threshold: Confidence threshold for guardrails.
            base_url: Custom API base URL (useful for Ollama).
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_context_chunks = max_context_chunks
        self.persona = persona
        self.api_key = api_key
        self.enable_guardrails = enable_guardrails
        self.base_url = base_url

        self.guardrails = Guardrails(hallucination_threshold=hallucination_threshold)

    async def generate(
        self,
        query: str,
        chunks: list[ScoredChunk],
        language: str = "English",
        template: str = "default",
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate an answer from retrieved chunks.

        Args:
            query: The user's question.
            chunks: Retrieved and ranked chunks.
            language: Desired response language.
            **kwargs: Extra parameters forwarded to the LLM call.

        Returns:
            GenerationResult with the answer, sources, and metadata.

        Raises:
            GenerationError: On LLM call failure.
        """
        # Limit context to max_context_chunks
        selected = chunks[: self.max_context_chunks]

        # Assemble context
        context_dicts = [
            {
                "content": c.content,
                "source": c.metadata.get("source", ""),
                "title": c.metadata.get("title", ""),
            }
            for c in selected
        ]
        context_str = format_context(context_dicts)

        # Build prompt
        messages = build_prompt_from_template(
            template_name=template,
            persona=self.persona,
            context=context_str,
            question=query,
            language=language,
        )

        # Call LLM
        answer, tokens_used = await self._call_llm(messages, **kwargs)

        # Extract citations
        sources = self._extract_citations(answer, selected)

        # Guardrails
        confidence = 1.0
        is_relevant = True
        if self.enable_guardrails:
            guardrail_result = self.guardrails.check(answer, context_str, query)
            confidence = guardrail_result["confidence"]
            is_relevant = guardrail_result["relevant"]

        return GenerationResult(
            answer=answer,
            sources=sources,
            confidence=confidence,
            tokens_used=tokens_used,
            model=self.model,
            is_relevant=is_relevant,
        )

    # ── LLM call dispatch ──────────────────────────────────────────────────

    async def _call_llm(self, messages: list[dict[str, str]], **kwargs: Any) -> tuple[str, int]:
        """Dispatch to the configured LLM provider.

        Returns:
            Tuple of (answer_text, tokens_used).
        """
        if self.provider == "openai":
            return await self._call_openai(messages, **kwargs)
        elif self.provider == "anthropic":
            return await self._call_anthropic(messages, **kwargs)
        elif self.provider == "ollama":
            return await self._call_ollama(messages, **kwargs)
        else:
            raise GenerationError(f"Unsupported LLM provider: {self.provider}")

    async def _call_openai(self, messages: list[dict[str, str]], **kwargs: Any) -> tuple[str, int]:
        try:
            from openai import AsyncOpenAI

            client_kwargs: dict[str, Any] = {}
            if self.api_key:
                client_kwargs["api_key"] = self.api_key
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            client = AsyncOpenAI(**client_kwargs)

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs,
            )

            answer = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            return answer, tokens_used

        except ImportError:
            raise GenerationError("openai package is required: pip install openai")
        except Exception as exc:
            raise GenerationError(f"OpenAI generation failed: {exc}") from exc

    async def _call_anthropic(self, messages: list[dict[str, str]], **kwargs: Any) -> tuple[str, int]:
        try:
            from anthropic import AsyncAnthropic

            client_kwargs: dict[str, Any] = {}
            if self.api_key:
                client_kwargs["api_key"] = self.api_key

            client = AsyncAnthropic(**client_kwargs)

            # Anthropic uses a separate system parameter
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)

            response = await client.messages.create(
                model=self.model,
                system=system_msg,
                messages=user_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs,
            )

            answer = response.content[0].text if response.content else ""
            tokens_used = (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
            return answer, tokens_used

        except ImportError:
            raise GenerationError("anthropic package is required: pip install anthropic")
        except Exception as exc:
            raise GenerationError(f"Anthropic generation failed: {exc}") from exc

    async def _call_ollama(self, messages: list[dict[str, str]], **kwargs: Any) -> tuple[str, int]:
        try:
            import httpx

            base_url = self.base_url or "http://localhost:11434"
            url = f"{base_url}/api/chat"

            payload = {
                "model": self.model,
                "messages": messages,
                "options": {"temperature": self.temperature},
                "stream": False,
            }

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            answer = data.get("message", {}).get("content", "")
            tokens_used = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
            return answer, tokens_used

        except ImportError:
            raise GenerationError("httpx package is required for Ollama: pip install httpx")
        except Exception as exc:
            raise GenerationError(f"Ollama generation failed: {exc}") from exc

    # ── Citation extraction ────────────────────────────────────────────────

    @staticmethod
    def _extract_citations(
        answer: str, chunks: list[ScoredChunk]
    ) -> list[dict[str, Any]]:
        """Extract source citations from the generated answer.

        Looks for [Source N] references and maps them back to chunks.

        Returns:
            List of source dicts with chunk metadata for cited sources.
        """
        pattern = re.compile(r"\[Source\s+(\d+)\]", re.IGNORECASE)
        cited_indices: set[int] = set()
        for match in pattern.finditer(answer):
            idx = int(match.group(1)) - 1  # Convert to 0-based
            if 0 <= idx < len(chunks):
                cited_indices.add(idx)

        sources = []
        for idx in sorted(cited_indices):
            chunk = chunks[idx]
            sources.append(
                {
                    "source_number": idx + 1,
                    "content_preview": chunk.content[:200],
                    "source": chunk.metadata.get("source", ""),
                    "title": chunk.metadata.get("title", ""),
                    "score": chunk.score,
                }
            )

        return sources
