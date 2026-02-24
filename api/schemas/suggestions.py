"""Schemas for smart suggestions endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    """A single smart suggestion for improving the RAG setup."""

    id: str = Field(..., description="Unique suggestion identifier")
    type: str = Field(
        ...,
        description="Suggestion category: setup, optimization, tip, or warning",
    )
    priority: int = Field(..., ge=1, le=5, description="Priority from 1 (low) to 5 (high)")
    title: str = Field(..., description="Short suggestion title")
    description: str = Field(..., description="Detailed suggestion description")
    action_label: str = Field(..., description="Call-to-action button label")
    action_href: str = Field(..., description="Link target for the action button")
    icon: str = Field(..., description="Lucide icon name")


class SuggestionsResponse(BaseModel):
    """Response containing a list of smart suggestions."""

    suggestions: list[Suggestion] = Field(default_factory=list)
