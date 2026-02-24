"""PluginManager — central facade for the Retrieva plugin system."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from core.plugin_system.discovery import DiscoveredPlugin, PluginDiscovery
from core.plugin_system.hooks import HookManager
from core.plugin_system.loader import PluginLoader
from core.plugin_system.manifest import PluginManifest
from core.plugin_system.registry import PluginRecord, PluginRegistry

logger = logging.getLogger(__name__)

# Default plugins directory (relative to project root).
_DEFAULT_PLUGINS_DIR = Path("plugins")

# Singleton.
_manager_instance: PluginManager | None = None


class PluginManager:
    """Orchestrate discovery, loading, lifecycle and hooks for all plugins."""

    def __init__(self, plugins_dir: Path | None = None) -> None:
        self.plugins_dir = plugins_dir or _DEFAULT_PLUGINS_DIR
        self.registry = PluginRegistry(self.plugins_dir / "registry.json")
        self.loader = PluginLoader()
        self.hooks = HookManager()

        # Manifest index (populated on initialize).
        self._manifests: dict[str, PluginManifest] = {}

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Discover plugins and synchronise the registry.

        Call once at application startup.
        """
        discovery = PluginDiscovery(self.plugins_dir)
        discovered: list[DiscoveredPlugin] = discovery.discover_all()

        for dp in discovered:
            m = dp.manifest
            self._manifests[m.name] = m

            existing = self.registry.get(m.name)
            if existing is None:
                # First time seen → register and enable by default.
                self.registry.register(
                    m.name,
                    plugin_type=m.type,
                    version=m.version,
                    source=dp.source,
                    path=str(m.source_path or ""),
                )
                logger.info("Registered new plugin: %s (%s)", m.name, m.type)
            else:
                # Already registered — update version if changed.
                if existing.version != m.version:
                    existing.version = m.version
                    self.registry.save()

        logger.info(
            "Plugin system initialised: %d plugins discovered", len(discovered)
        )

    # ------------------------------------------------------------------
    # Plugin access (lazy loading)
    # ------------------------------------------------------------------

    def get_plugin(
        self,
        plugin_type: str,
        name: str,
        config: dict[str, Any] | None = None,
    ) -> Any:
        """Return a loaded, configured instance of the named plugin.

        Raises ``PluginNotFoundError`` if the plugin is unknown or disabled.
        """
        from core.exceptions import PluginNotFoundError

        manifest = self._manifests.get(name)
        if manifest is None:
            raise PluginNotFoundError(f"Plugin '{name}' not found")

        if manifest.type != plugin_type:
            raise PluginNotFoundError(
                f"Plugin '{name}' is type '{manifest.type}', expected '{plugin_type}'"
            )

        if not self.registry.is_enabled(name):
            raise PluginNotFoundError(f"Plugin '{name}' is disabled")

        # Merge stored config with caller overrides.
        stored_cfg = (self.registry.get(name) or PluginRecord({})).config
        merged_config = {**stored_cfg, **(config or {})}

        try:
            instance = self.loader.get_instance(manifest, merged_config)
            return instance
        except Exception as exc:
            self.registry.set_error(name, str(exc))
            logger.error("Failed to load plugin '%s': %s", name, exc, exc_info=True)
            raise

    def get_plugins_by_type(self, plugin_type: str) -> list[dict[str, Any]]:
        """Return metadata dicts for all plugins of *plugin_type*."""
        result: list[dict[str, Any]] = []
        for name, manifest in self._manifests.items():
            if manifest.type != plugin_type:
                continue
            rec = self.registry.get(name)
            result.append({
                "name": name,
                "type": manifest.type,
                "version": manifest.version,
                "description": manifest.description,
                "status": rec.status if rec else "unknown",
                "source": rec.source if rec else "unknown",
                "bundled": manifest.bundled,
                "config_schema": manifest.config_schema,
                "tags": manifest.tags,
            })
        return result

    def list_all_plugins(self) -> list[dict[str, Any]]:
        """Return metadata for every known plugin."""
        result: list[dict[str, Any]] = []
        for name, manifest in sorted(self._manifests.items()):
            rec = self.registry.get(name)
            result.append({
                "name": name,
                "type": manifest.type,
                "version": manifest.version,
                "description": manifest.description,
                "author": manifest.author,
                "status": rec.status if rec else "unknown",
                "source": rec.source if rec else "unknown",
                "bundled": manifest.bundled,
                "config_schema": manifest.config_schema,
                "config": rec.config if rec else {},
                "tags": manifest.tags,
            })
        return result

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def enable_plugin(self, name: str) -> bool:
        ok = self.registry.enable(name)
        if ok:
            logger.info("Enabled plugin: %s", name)
        return ok

    def disable_plugin(self, name: str) -> bool:
        self.loader.invalidate(name)
        ok = self.registry.disable(name)
        if ok:
            logger.info("Disabled plugin: %s", name)
        return ok

    def install_plugin(self, source: str) -> PluginManifest:
        """Install a plugin from a local directory path.

        Copies the plugin folder into the ``plugins/`` directory and registers it.
        """
        source_path = Path(source)
        if not source_path.is_dir():
            raise FileNotFoundError(f"Plugin source not found: {source}")

        yaml_path = source_path / "plugin.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"No plugin.yaml in {source}")

        manifest = PluginManifest.from_yaml(yaml_path)
        dest = self.plugins_dir / f"{manifest.type}s" / manifest.name

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source_path, dest)

        manifest.source_path = dest
        self._manifests[manifest.name] = manifest
        self.registry.register(
            manifest.name,
            plugin_type=manifest.type,
            version=manifest.version,
            source="local",
            path=str(dest),
        )
        logger.info("Installed plugin: %s from %s", manifest.name, source)
        return manifest

    def uninstall_plugin(self, name: str, *, keep_data: bool = False) -> bool:
        """Uninstall a plugin by removing it from disk and registry."""
        manifest = self._manifests.get(name)
        if manifest is None:
            return False

        if manifest.bundled:
            logger.warning("Cannot uninstall bundled plugin: %s", name)
            return False

        self.loader.invalidate(name)

        if not keep_data and manifest.source_path and manifest.source_path.exists():
            shutil.rmtree(manifest.source_path)

        self._manifests.pop(name, None)
        self.registry.unregister(name)
        logger.info("Uninstalled plugin: %s", name)
        return True

    def update_plugin_config(self, name: str, config: dict[str, Any]) -> bool:
        """Persist new configuration for a plugin."""
        self.loader.invalidate(name)
        return self.registry.update_config(name, config)


def get_plugin_manager(plugins_dir: Path | None = None) -> PluginManager:
    """Return the global PluginManager singleton, creating it if needed."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = PluginManager(plugins_dir)
    return _manager_instance
