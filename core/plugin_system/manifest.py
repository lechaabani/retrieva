"""Pydantic model for plugin.yaml manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from core.plugin_system.protocols import PLUGIN_TYPE_PROTOCOLS


class PluginManifest(BaseModel):
    """Metadata parsed from a plugin's ``plugin.yaml``."""

    name: str
    type: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    entry_point: str  # "module:ClassName"
    config_schema: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    min_retrieva_version: str = "0.1.0"
    hooks: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    bundled: bool = False

    # Set at load time, not from YAML.
    _source_path: Path | None = None

    @property
    def source_path(self) -> Path | None:
        return self._source_path

    @source_path.setter
    def source_path(self, value: Path) -> None:
        self._source_path = value

    def validate_type(self) -> None:
        """Raise ValueError if *type* is not a recognised plugin type."""
        if self.type not in PLUGIN_TYPE_PROTOCOLS:
            valid = ", ".join(sorted(PLUGIN_TYPE_PROTOCOLS))
            raise ValueError(
                f"Unknown plugin type '{self.type}'. Must be one of: {valid}"
            )

    @classmethod
    def from_yaml(cls, path: Path) -> "PluginManifest":
        """Load a manifest from a ``plugin.yaml`` file."""
        with open(path) as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid plugin.yaml at {path}")
        manifest = cls(**data)
        manifest.source_path = path.parent
        manifest.validate_type()
        return manifest
