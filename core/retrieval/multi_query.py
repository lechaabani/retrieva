"""Multi-query expansion for improved retrieval recall.

Uses an LLM to generate multiple reformulations of the user's query,
then searches with each variant and merges the results.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from core.exceptions import GenerationError

logger = logging.getLogger(__name__)

_EXPANSION_PROMPT = """\
You are a helpful search query expansion assistant.

Given the following user search query, generate exactly 3 alternative
reformulations that capture different aspects or phrasings of the same
information need.  Each reformulation should be a complete, standalone
search query.

Rules:
- Output ONLY the 3 queries, one per line, numbered 1-3.
- Do not include any explanation or preamble.
- Keep each query concise (under 30 words).

User query: {query}
"""


class MultiQueryExpander:
    """Generates multiple reformulations of a query using an LLM.

    Falls back to returning the original query as a single-element list
    if the LLM call fails for any reason.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_expansions: int = 3,
    ) -> None:
        """
        Args:
            provider: LLM provider ("openai", "anthropic", "ollama").
            model: Model identifier.
            api_key: API key (falls back to env var).
            base_url: Custom API base URL.
            temperature: Sampling temperature for diversity.
            max_expansions: Number of query variants to generate.
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_expansions = max_expansions

    async def expand(self, query: str) -> list[str]:
        """Generate query reformulations.

        Args:
            query: The original user query.

        Returns:
            A list of query strings, always including the original query
            as the first element followed by the generated variants.
            On failure, returns ``[query]``.
        """
        try:
            variants = await self._generate_variants(query)
            # Always include the original as the first query
            result = [query] + [v for v in variants if v.lower().strip() != query.lower().strip()]
            logger.info(
                "Multi-query expansion: original=%r -> %d variants",
                query, len(result) - 1,
            )
            return result
        except Exception as exc:
            logger.warning(
                "Multi-query expansion failed, using original query: %s", exc
            )
            return [query]

    async def _generate_variants(self, query: str) -> list[str]:
        """Call the LLM to produce reformulations."""
        prompt = _EXPANSION_PROMPT.format(query=query)
        messages = [{"role": "user", "content": prompt}]

        response_text = await self._call_llm(messages)
        return self._parse_variants(response_text)

    def _parse_variants(self, response: str) -> list[str]:
        """Extract numbered queries from the LLM response."""
        lines = response.strip().split("\n")
        variants: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Strip leading number/bullet: "1. ...", "1) ...", "- ..."
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
            cleaned = re.sub(r"^[-*]\s*", "", cleaned)
            cleaned = cleaned.strip().strip('"').strip("'")
            if cleaned and len(cleaned) > 3:
                variants.append(cleaned)

        return variants[: self.max_expansions]

    async def _call_llm(self, messages: list[dict[str, str]]) -> str:
        """Dispatch to the configured LLM provider."""
        if self.provider == "openai":
            return await self._call_openai(messages)
        elif self.provider == "anthropic":
            return await self._call_anthropic(messages)
        elif self.provider == "ollama":
            return await self._call_ollama(messages)
        else:
            raise GenerationError(f"Unsupported LLM provider: {self.provider}")

    async def _call_openai(self, messages: list[dict[str, str]]) -> str:
        from openai import AsyncOpenAI

        kwargs: dict[str, Any] = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url

        client = AsyncOpenAI(**kwargs)
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=256,
        )
        return response.choices[0].message.content or ""

    async def _call_anthropic(self, messages: list[dict[str, str]]) -> str:
        from anthropic import AsyncAnthropic

        kwargs: dict[str, Any] = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key

        client = AsyncAnthropic(**kwargs)
        response = await client.messages.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=256,
        )
        return response.content[0].text if response.content else ""

    async def _call_ollama(self, messages: list[dict[str, str]]) -> str:
        import httpx

        base_url = self.base_url or "http://localhost:11434"
        url = f"{base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "options": {"temperature": self.temperature},
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return data.get("message", {}).get("content", "")
