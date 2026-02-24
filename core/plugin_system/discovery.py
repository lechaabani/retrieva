"""Plugin discovery — scan folders and entry_points."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.plugin_system.manifest import PluginManifest

logger = logging.getLogger(__name__)


class DiscoveredPlugin:
    """A plugin found by the discovery process."""

    __slots__ = ("manifest", "source")

    def __init__(self, manifest: PluginManifest, source: str = "local") -> None:
        self.manifest = manifest
        self.source = source  # "bundled" | "local" | "entry_point"


class PluginDiscovery:
    """Discover plugins from the filesystem and installed packages."""

    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = plugins_dir

    def discover_all(self) -> list[DiscoveredPlugin]:
        """Return every discoverable plugin."""
        plugins: list[DiscoveredPlugin] = []
        plugins.extend(self._scan_directory())
        plugins.extend(self._scan_entry_points())
        return plugins

    # ------------------------------------------------------------------
    # Folder scanning
    # ------------------------------------------------------------------

    def _scan_directory(self) -> list[DiscoveredPlugin]:
        """Walk ``plugins/<type>/<name>/plugin.yaml``."""
        found: list[DiscoveredPlugin] = []
        if not self.plugins_dir.exists():
            return found

        for type_dir in sorted(self.plugins_dir.iterdir()):
            if not type_dir.is_dir() or type_dir.name.startswith("."):
                continue
            # Could be a type grouping dir (chunkers/) or a flat plugin dir.
            yaml_file = type_dir / "plugin.yaml"
            if yaml_file.exists():
                self._try_load(yaml_file, found)
            else:
                # Nested: plugins/<type>/<name>/plugin.yaml
                for plugin_dir in sorted(type_dir.iterdir()):
                    if not plugin_dir.is_dir():
                        continue
                    nested_yaml = plugin_dir / "plugin.yaml"
                    if nested_yaml.exists():
                        self._try_load(nested_yaml, found)

        return found

    def _try_load(
        self, yaml_path: Path, acc: list[DiscoveredPlugin]
    ) -> None:
        try:
            manifest = PluginManifest.from_yaml(yaml_path)
            source = "bundled" if manifest.bundled else "local"
            acc.append(DiscoveredPlugin(manifest, source))
        except Exception:
            logger.warning("Failed to load plugin from %s", yaml_path, exc_info=True)

    # ------------------------------------------------------------------
    # Entry-points (pip-installed packages)
    # ------------------------------------------------------------------

    def _scan_entry_points(self) -> list[DiscoveredPlugin]:
        """Discover plugins registered via ``[project.entry-points."retrieva.plugins"]``."""
        found: list[DiscoveredPlugin] = []
        try:
            from importlib.metadata import entry_points

            eps = entry_points(group="retrieva.plugins")
            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    # Expect the class to expose a ``plugin_manifest`` classmethod or attribute.
                    if hasattr(plugin_cls, "plugin_manifest"):
                        manifest_data: dict[str, Any] = plugin_cls.plugin_manifest()
                        manifest = PluginManifest(**manifest_data)
                        found.append(DiscoveredPlugin(manifest, source="entry_point"))
                    else:
                        logger.warning(
                            "Entry-point %s does not expose plugin_manifest()", ep.name
                        )
                except Exception:
                    logger.warning(
                        "Failed to load entry-point plugin %s", ep.name, exc_info=True
                    )
        except Exception:
            pass  # No entry-points support or none defined.

        return found
