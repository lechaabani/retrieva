"""Dynamic plugin loader — import, validate, and cache plugin instances."""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Any

from core.plugin_system.manifest import PluginManifest
from core.plugin_system.protocols import PLUGIN_TYPE_PROTOCOLS

logger = logging.getLogger(__name__)


class PluginLoader:
    """Import plugin classes and create configured instances."""

    def __init__(self) -> None:
        self._class_cache: dict[str, type] = {}
        self._instance_cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_class(self, manifest: PluginManifest) -> type:
        """Import and return the plugin class described by *manifest*.

        The class is cached by plugin name.
        """
        if manifest.name in self._class_cache:
            return self._class_cache[manifest.name]

        module_name, class_name = self._parse_entry_point(manifest.entry_point)
        plugin_dir = manifest.source_path

        # Temporarily add the plugin directory to sys.path so relative
        # imports inside the plugin module resolve correctly.
        added_to_path = False
        if plugin_dir and str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
            added_to_path = True

        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
        except Exception as exc:
            raise ImportError(
                f"Cannot load plugin '{manifest.name}' "
                f"(entry_point={manifest.entry_point}): {exc}"
            ) from exc
        finally:
            if added_to_path:
                sys.path.remove(str(plugin_dir))

        self._class_cache[manifest.name] = cls
        return cls

    def get_instance(
        self,
        manifest: PluginManifest,
        config: dict[str, Any] | None = None,
        *,
        force_new: bool = False,
    ) -> Any:
        """Return a configured plugin instance (cached by default)."""
        cache_key = manifest.name
        if not force_new and cache_key in self._instance_cache:
            return self._instance_cache[cache_key]

        cls = self.load_class(manifest)

        # Try to pass config to __init__; fall back to no-arg constructor.
        try:
            instance = cls(config=config or {})
        except TypeError:
            instance = cls()

        self._instance_cache[cache_key] = instance
        return instance

    def validate_protocol(self, manifest: PluginManifest, instance: Any) -> bool:
        """Check that *instance* satisfies the Protocol for its declared type."""
        protocol = PLUGIN_TYPE_PROTOCOLS.get(manifest.type)
        if protocol is None:
            logger.warning("No protocol defined for type '%s'", manifest.type)
            return True  # No protocol to check against.
        return isinstance(instance, protocol)

    def invalidate(self, name: str) -> None:
        """Remove a plugin from both caches."""
        self._class_cache.pop(name, None)
        self._instance_cache.pop(name, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_entry_point(entry_point: str) -> tuple[str, str]:
        """Parse ``"module.path:ClassName"`` into (module, class)."""
        if ":" not in entry_point:
            raise ValueError(
                f"Invalid entry_point '{entry_point}'. Expected 'module:ClassName'."
            )
        module_name, class_name = entry_point.rsplit(":", 1)
        return module_name, class_name
