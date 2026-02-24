"""Retrieva Plugin System — WordPress-like modular architecture."""

from core.plugin_system.protocols import (
    ChunkerPlugin,
    ConnectorPlugin,
    EmbedderPlugin,
    ExtractorPlugin,
    GeneratorPlugin,
    GuardrailPlugin,
    RetrieverPlugin,
    TemplatePlugin,
    PLUGIN_TYPE_PROTOCOLS,
)
from core.plugin_system.manifest import PluginManifest
from core.plugin_system.registry import PluginRegistry
from core.plugin_system.loader import PluginLoader
from core.plugin_system.hooks import HookManager
from core.plugin_system.manager import PluginManager, get_plugin_manager

__all__ = [
    "ChunkerPlugin",
    "ConnectorPlugin",
    "EmbedderPlugin",
    "ExtractorPlugin",
    "GeneratorPlugin",
    "GuardrailPlugin",
    "RetrieverPlugin",
    "TemplatePlugin",
    "PLUGIN_TYPE_PROTOCOLS",
    "PluginManifest",
    "PluginRegistry",
    "PluginLoader",
    "HookManager",
    "PluginManager",
    "get_plugin_manager",
]
