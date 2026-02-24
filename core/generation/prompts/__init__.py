"""Prompt template registry for the generation engine.

Provides multiple named prompt templates (default, concise, detailed,
structured, multilingual) that can be selected at query time.
"""

from __future__ import annotations

from typing import Any

from core.generation.prompts.default import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT,
    build_prompt,
    format_context,
)

# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, str]] = {
    "default": {
        "system": DEFAULT_SYSTEM_PROMPT,
        "user": DEFAULT_USER_PROMPT,
    },
    "concise": {
        "system": (
            "{persona}\n\n"
            "Instructions:\n"
            "- Answer ONLY from the provided context.\n"
            "- Be extremely brief: 1-3 sentences maximum.\n"
            "- If unsure, say so in one sentence.\n"
            "- Respond in {language}."
        ),
        "user": (
            "Context:\n---\n{context}\n---\n\n"
            "Question: {question}\n\n"
            "Answer concisely:"
        ),
    },
    "detailed": {
        "system": (
            "{persona}\n\n"
            "Instructions:\n"
            "- Provide a thorough, well-structured answer based on the context.\n"
            "- Use headings and bullet points where appropriate.\n"
            "- Cite sources as [Source N] for each claim.\n"
            "- If the context is insufficient, explain what information is missing.\n"
            "- Respond in {language}."
        ),
        "user": (
            "Context:\n---\n{context}\n---\n\n"
            "Question: {question}\n\n"
            "Provide a detailed, well-organized answer:"
        ),
    },
    "structured": {
        "system": (
            "{persona}\n\n"
            "Instructions:\n"
            "- Answer based ONLY on the provided context.\n"
            "- Structure your response as JSON with these keys:\n"
            '  - "answer": the main answer text\n'
            '  - "confidence": your confidence level ("high", "medium", "low")\n'
            '  - "sources_used": list of source numbers referenced\n'
            '  - "key_points": list of key takeaways\n'
            "- Respond in {language}."
        ),
        "user": (
            "Context:\n---\n{context}\n---\n\n"
            "Question: {question}\n\n"
            "Respond in JSON format:"
        ),
    },
    "multilingual": {
        "system": (
            "{persona}\n\n"
            "Instructions:\n"
            "- Answer based ONLY on the provided context.\n"
            "- IMPORTANT: Detect the language of the question and respond in the SAME language.\n"
            "- If the context is in a different language, translate relevant information.\n"
            "- Cite sources as [Source N].\n"
            "- Override language hint: {language}."
        ),
        "user": (
            "Context:\n---\n{context}\n---\n\n"
            "Question: {question}"
        ),
    },
}


def get_template(name: str = "default") -> dict[str, str]:
    """Return a named prompt template.

    Args:
        name: Template name. Falls back to ``"default"`` if not found.

    Returns:
        Dict with ``"system"`` and ``"user"`` template strings.
    """
    return _TEMPLATES.get(name, _TEMPLATES["default"])


def list_templates() -> list[str]:
    """Return the list of available template names."""
    return list(_TEMPLATES.keys())


def build_prompt_from_template(
    template_name: str,
    persona: str,
    context: str,
    question: str,
    language: str = "English",
) -> list[dict[str, str]]:
    """Build an OpenAI-compatible messages list using a named template.

    Args:
        template_name: Name of the template to use.
        persona: System persona description.
        context: Pre-formatted context string.
        question: The user's question.
        language: Response language.

    Returns:
        A list of message dicts with ``role`` and ``content`` keys.
    """
    tmpl = get_template(template_name)
    system_content = tmpl["system"].format(persona=persona, language=language)
    user_content = tmpl["user"].format(context=context, question=question)

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


__all__ = [
    "build_prompt",
    "build_prompt_from_template",
    "format_context",
    "get_template",
    "list_templates",
]
