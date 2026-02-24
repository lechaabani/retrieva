"""Default prompt templates for the generation engine."""

from __future__ import annotations

from typing import Any

DEFAULT_SYSTEM_PROMPT = (
    "{persona}\n\n"
    "Instructions:\n"
    "- Answer the question based ONLY on the provided context.\n"
    "- If the context does not contain enough information, say so clearly.\n"
    "- Cite your sources by referencing [Source N] where N is the chunk number.\n"
    "- Be concise and accurate.\n"
    "- Respond in {language}."
)

DEFAULT_USER_PROMPT = (
    "Context:\n"
    "---\n"
    "{context}\n"
    "---\n\n"
    "Question: {question}"
)


def format_context(chunks: list[dict[str, Any]]) -> str:
    """Format retrieved chunks into a numbered context block.

    Args:
        chunks: List of chunk dicts, each with at least a ``content`` key
                and optionally ``source`` or ``title`` in metadata.

    Returns:
        A formatted string with each chunk labelled [Source N].
    """
    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content", "")
        source = chunk.get("source", chunk.get("title", ""))
        header = f"[Source {i}]"
        if source:
            header += f" ({source})"
        parts.append(f"{header}\n{content}")
    return "\n\n".join(parts)


def build_prompt(
    persona: str,
    context: str,
    question: str,
    language: str = "English",
) -> list[dict[str, str]]:
    """Build an OpenAI-compatible messages list for the generation call.

    Args:
        persona: System persona description.
        context: Pre-formatted context string (from ``format_context``).
        question: The user's question.
        language: Response language.

    Returns:
        A list of message dicts with ``role`` and ``content`` keys.
    """
    system_content = DEFAULT_SYSTEM_PROMPT.format(persona=persona, language=language)
    user_content = DEFAULT_USER_PROMPT.format(context=context, question=question)

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
