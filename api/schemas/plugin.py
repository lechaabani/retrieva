"""Pydantic schemas for plugin management."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class PluginInfo(BaseModel):
    """Full plugin metadata and configuration."""

    name: str
    type: str
    version: str
    description: str = ""
    author: str = ""
    status: str = "enabled"  # enabled | disabled | error
    source: str = "bundled"  # bundled | local | pypi | git
    bundled: bool = False
    config_schema: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class PluginListResponse(BaseModel):
    """Response for listing all plugins."""

    plugins: list[PluginInfo]
    total: int


class PluginInstallRequest(BaseModel):
    """Request to install a plugin from a source."""

    source: str  # local path, git url, or pypi package name


class PluginConfigRequest(BaseModel):
    """Request to update a plugin's configuration."""

    config: dict[str, Any]
