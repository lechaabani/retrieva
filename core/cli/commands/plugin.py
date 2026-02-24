"""CLI commands for plugin management.

Usage:
    retrieva plugin list
    retrieva plugin info <name>
    retrieva plugin init <name> --type <type>
    retrieva plugin install <source>
    retrieva plugin enable <name>
    retrieva plugin disable <name>
    retrieva plugin validate <path>
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click

from core.plugin_system.protocols import PLUGIN_TYPE_PROTOCOLS

# ---------------------------------------------------------------------------
# Plugin type -> skeleton code mapping
# ---------------------------------------------------------------------------

_SKELETON_CODE: dict[str, str] = {
    "chunker": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Chunker plugin — split text into chunks for embedding."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    def chunk(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
''',
    "embedder": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Embedder plugin — generate vector embeddings from text."""

    dimensions: int = 384

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError
''',
    "connector": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Connector plugin — pull documents from an external data source."""

    name: str = "{plugin_name}"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    async def pull(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def test_connection(self) -> bool:
        raise NotImplementedError
''',
    "extractor": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Extractor plugin — extract text content from a file."""

    supported_extensions: list[str] = []

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    async def extract(self, source: Any) -> Any:
        raise NotImplementedError
''',
    "retriever": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Retriever plugin — search a collection and return ranked chunks."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    async def search(
        self,
        query: str,
        collection_id: str,
        top_k: int = 10,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
''',
    "generator": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Generator plugin — call an LLM and return generated text."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    async def generate(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> tuple[str, int]:
        raise NotImplementedError
''',
    "guardrail": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Guardrail plugin — validate generated answers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    def check(
        self,
        answer: str,
        context: str,
        query: str,
    ) -> dict[str, Any]:
        raise NotImplementedError
''',
    "template": '''\
"""Plugin entry point."""

from __future__ import annotations

from typing import Any


class {class_name}:
    """Template plugin — embeddable UI template."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}

    def get_assets(self) -> dict[str, str]:
        raise NotImplementedError

    def render(self, config: dict[str, Any]) -> str:
        raise NotImplementedError
''',
}

_PLUGIN_YAML_TEMPLATE = """\
name: {name}
type: {type}
version: "0.1.0"
description: "A custom {type} plugin"
author: ""
license: "MIT"
entry_point: "plugin:{class_name}"
config_schema: {{}}
dependencies: []
min_retrieva_version: "0.1.0"
tags: []
"""

_README_TEMPLATE = """\
# {name}

A custom **{type}** plugin for Retrieva.

## Installation

```bash
retrieva plugin install /path/to/{name}
```

## Configuration

_No configuration options yet._
"""


def _name_to_class(name: str) -> str:
    """Convert a kebab/snake-case plugin name to PascalCase class name."""
    return "".join(part.capitalize() for part in name.replace("-", "_").split("_"))


def _get_manager():  # noqa: ANN202
    from core.plugin_system.manager import get_plugin_manager

    mgr = get_plugin_manager()
    mgr.initialize()
    return mgr


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group()
def plugin() -> None:
    """Manage Retrieva plugins."""


# -- list -------------------------------------------------------------------


@plugin.command("list")
def list_plugins() -> None:
    """List all registered plugins."""
    mgr = _get_manager()
    plugins = mgr.list_all_plugins()

    if not plugins:
        click.echo("No plugins found.")
        return

    # Column widths.
    header = ("Name", "Type", "Version", "Status", "Source")
    rows: list[tuple[str, ...]] = []
    for p in plugins:
        rows.append((
            p["name"],
            p["type"],
            p["version"],
            p.get("status", "unknown"),
            p.get("source", "unknown"),
        ))

    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(header)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)

    click.echo(fmt.format(*header))
    click.echo(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        click.echo(fmt.format(*row))


# -- info -------------------------------------------------------------------


@plugin.command("info")
@click.argument("name")
def info(name: str) -> None:
    """Show detailed information about a plugin."""
    mgr = _get_manager()
    all_plugins = mgr.list_all_plugins()
    match = [p for p in all_plugins if p["name"] == name]

    if not match:
        click.echo(f"Plugin '{name}' not found.", err=True)
        raise SystemExit(1)

    p: dict[str, Any] = match[0]
    click.echo(f"Name:         {p['name']}")
    click.echo(f"Type:         {p['type']}")
    click.echo(f"Version:      {p['version']}")
    click.echo(f"Status:       {p.get('status', 'unknown')}")
    click.echo(f"Source:       {p.get('source', 'unknown')}")
    click.echo(f"Author:       {p.get('author', '')}")
    click.echo(f"Description:  {p.get('description', '')}")
    click.echo(f"Bundled:      {p.get('bundled', False)}")
    click.echo(f"Tags:         {', '.join(p.get('tags', [])) or '—'}")

    config_schema = p.get("config_schema", {})
    if config_schema:
        click.echo("Config schema:")
        for key, val in config_schema.items():
            click.echo(f"  {key}: {val}")

    config = p.get("config", {})
    if config:
        click.echo("Current config:")
        for key, val in config.items():
            click.echo(f"  {key}: {val}")


# -- init -------------------------------------------------------------------


@plugin.command("init")
@click.argument("name")
@click.option(
    "--type",
    "plugin_type",
    required=True,
    type=click.Choice(sorted(PLUGIN_TYPE_PROTOCOLS.keys()), case_sensitive=False),
    help="Plugin type.",
)
def init(name: str, plugin_type: str) -> None:
    """Scaffold a new plugin directory."""
    base_dir = Path("plugins") / f"{plugin_type}s" / name
    if base_dir.exists():
        click.echo(f"Directory already exists: {base_dir}", err=True)
        raise SystemExit(1)

    base_dir.mkdir(parents=True)

    class_name = _name_to_class(name)

    # plugin.yaml
    yaml_path = base_dir / "plugin.yaml"
    yaml_path.write_text(
        _PLUGIN_YAML_TEMPLATE.format(name=name, type=plugin_type, class_name=class_name)
    )

    # plugin.py
    py_path = base_dir / "plugin.py"
    skeleton = _SKELETON_CODE.get(plugin_type, "")
    py_path.write_text(skeleton.format(class_name=class_name, plugin_name=name))

    # README.md
    readme_path = base_dir / "README.md"
    readme_path.write_text(_README_TEMPLATE.format(name=name, type=plugin_type))

    click.echo(f"Scaffolded plugin '{name}' at {base_dir}/")
    click.echo(f"  {yaml_path}")
    click.echo(f"  {py_path}")
    click.echo(f"  {readme_path}")


# -- install ----------------------------------------------------------------


@plugin.command("install")
@click.argument("source")
def install(source: str) -> None:
    """Install a plugin from a local path."""
    mgr = _get_manager()
    try:
        manifest = mgr.install_plugin(source)
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"Installed plugin '{manifest.name}' (v{manifest.version}).")


# -- enable -----------------------------------------------------------------


@plugin.command("enable")
@click.argument("name")
def enable(name: str) -> None:
    """Enable a disabled plugin."""
    mgr = _get_manager()
    if mgr.enable_plugin(name):
        click.echo(f"Enabled plugin '{name}'.")
    else:
        click.echo(f"Could not enable plugin '{name}'. Is it registered?", err=True)
        raise SystemExit(1)


# -- disable ----------------------------------------------------------------


@plugin.command("disable")
@click.argument("name")
def disable(name: str) -> None:
    """Disable a plugin."""
    mgr = _get_manager()
    if mgr.disable_plugin(name):
        click.echo(f"Disabled plugin '{name}'.")
    else:
        click.echo(f"Could not disable plugin '{name}'. Is it registered?", err=True)
        raise SystemExit(1)


# -- validate ---------------------------------------------------------------


@plugin.command("validate")
@click.argument("path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
def validate(path: str) -> None:
    """Validate a plugin directory."""
    plugin_dir = Path(path)
    errors: list[str] = []

    # 1. Check plugin.yaml exists.
    yaml_path = plugin_dir / "plugin.yaml"
    if not yaml_path.exists():
        click.echo(f"FAIL: plugin.yaml not found in {plugin_dir}", err=True)
        raise SystemExit(1)

    # 2. Parse manifest.
    from core.plugin_system.manifest import PluginManifest

    try:
        manifest = PluginManifest.from_yaml(yaml_path)
    except Exception as exc:
        click.echo(f"FAIL: Invalid plugin.yaml — {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"  Manifest OK: {manifest.name} ({manifest.type} v{manifest.version})")

    # 3. Try to import the entry_point class.
    from core.plugin_system.loader import PluginLoader

    loader = PluginLoader()
    try:
        cls = loader.load_class(manifest)
    except ImportError as exc:
        errors.append(f"Cannot import entry_point: {exc}")
        cls = None

    if cls is not None:
        click.echo(f"  Entry point OK: {manifest.entry_point} -> {cls.__name__}")

        # 4. Check protocol conformance.
        try:
            instance = cls(config={})
        except TypeError:
            instance = cls()

        if loader.validate_protocol(manifest, instance):
            click.echo(f"  Protocol OK: satisfies {manifest.type.capitalize()}Plugin")
        else:
            errors.append(
                f"Class '{cls.__name__}' does not satisfy the "
                f"{manifest.type.capitalize()}Plugin protocol"
            )

    if errors:
        click.echo("")
        for err in errors:
            click.echo(f"  ERROR: {err}", err=True)
        raise SystemExit(1)

    click.echo("")
    click.echo("Validation passed.")
