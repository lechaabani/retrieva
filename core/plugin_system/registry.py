"""Persistent plugin registry backed by a JSON file."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default location relative to project root.
DEFAULT_REGISTRY_PATH = Path("plugins/registry.json")


class PluginRecord:
    """In-memory representation of one plugin's registry entry."""

    __slots__ = (
        "name", "type", "version", "status", "source", "path",
        "installed_at", "config",
    )

    def __init__(self, data: dict[str, Any], name: str = "") -> None:
        self.name: str = name or data.get("name", "")
        self.type: str = data.get("type", "")
        self.version: str = data.get("version", "0.0.0")
        self.status: str = data.get("status", "enabled")  # enabled | disabled | error
        self.source: str = data.get("source", "local")     # bundled | local | pypi | git
        self.path: str = data.get("path", "")
        self.installed_at: str = data.get(
            "installed_at", datetime.now(timezone.utc).isoformat()
        )
        self.config: dict[str, Any] = data.get("config", {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "version": self.version,
            "status": self.status,
            "source": self.source,
            "path": self.path,
            "installed_at": self.installed_at,
            "config": self.config,
        }


class PluginRegistry:
    """CRUD wrapper around ``plugins/registry.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_REGISTRY_PATH
        self._plugins: dict[str, PluginRecord] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            self._plugins = {}
            return
        try:
            raw = json.loads(self._path.read_text())
            plugins_data = raw.get("plugins", raw)
            if isinstance(plugins_data, dict):
                self._plugins = {
                    name: PluginRecord(data, name=name)
                    for name, data in plugins_data.items()
                }
            else:
                # Legacy v1 format (list).
                self._plugins = {}
        except Exception:
            logger.warning("Could not parse registry at %s", self._path, exc_info=True)
            self._plugins = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "2.0",
            "plugins": {name: rec.to_dict() for name, rec in self._plugins.items()},
        }
        self._path.write_text(json.dumps(data, indent=2) + "\n")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_plugins(self) -> dict[str, PluginRecord]:
        return dict(self._plugins)

    def get(self, name: str) -> PluginRecord | None:
        return self._plugins.get(name)

    def register(
        self,
        name: str,
        *,
        plugin_type: str,
        version: str,
        source: str,
        path: str,
        config: dict[str, Any] | None = None,
    ) -> PluginRecord:
        rec = PluginRecord({
            "type": plugin_type,
            "version": version,
            "status": "enabled",
            "source": source,
            "path": path,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "config": config or {},
        }, name=name)
        self._plugins[name] = rec
        self.save()
        return rec

    def enable(self, name: str) -> bool:
        rec = self._plugins.get(name)
        if rec is None:
            return False
        rec.status = "enabled"
        self.save()
        return True

    def disable(self, name: str) -> bool:
        rec = self._plugins.get(name)
        if rec is None:
            return False
        rec.status = "disabled"
        self.save()
        return True

    def set_error(self, name: str, detail: str = "") -> None:
        rec = self._plugins.get(name)
        if rec:
            rec.status = "error"
            if detail:
                rec.config["_error"] = detail
            self.save()

    def unregister(self, name: str) -> bool:
        if name in self._plugins:
            del self._plugins[name]
            self.save()
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        rec = self._plugins.get(name)
        return rec is not None and rec.status == "enabled"

    def update_config(self, name: str, config: dict[str, Any]) -> bool:
        rec = self._plugins.get(name)
        if rec is None:
            return False
        rec.config = config
        self.save()
        return True
