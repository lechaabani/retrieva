"""Pydantic schemas for template endpoints."""

from pydantic import BaseModel


class TemplateInfo(BaseModel):
    """Metadata for a standalone HTML template."""

    name: str
    title: str
    description: str
    template_type: str  # "chatbot", "search", "faq"
    files: list[str]


class TemplateDownloadRequest(BaseModel):
    """Configuration payload for generating a configured template zip."""

    api_url: str = "http://localhost:8000"
    api_key: str = ""
    widget_id: str = ""
    config: dict = {}
