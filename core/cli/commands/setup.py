"""CLI command for initial platform setup.

Usage:
    retrieva setup
"""

from __future__ import annotations

import hashlib
import secrets
import subprocess
import sys
import uuid

import click


@click.command()
def setup() -> None:
    """Run initial platform setup (migrations, default tenant, API key, plugins)."""
    click.echo("Setting up Retrieva...\n")

    # ------------------------------------------------------------------
    # 1. Run Alembic migrations
    # ------------------------------------------------------------------
    click.echo("[1/4] Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            click.echo(result.stdout.strip())
        click.echo("  Migrations complete.")
    except subprocess.CalledProcessError as exc:
        click.echo(f"  Warning: migrations failed — {exc.stderr.strip()}", err=True)
        click.echo("  Continuing setup (database may already be up to date).\n")
    except FileNotFoundError:
        click.echo("  Warning: alembic not found; skipping migrations.\n", err=True)

    # ------------------------------------------------------------------
    # 2. Create default tenant
    # ------------------------------------------------------------------
    click.echo("[2/4] Creating default tenant...")
    tenant_id: uuid.UUID | None = None
    try:
        from workers.db import get_sync_session
        from api.models.tenant import Tenant

        with get_sync_session() as session:
            existing = session.query(Tenant).filter_by(slug="default").first()
            if existing:
                click.echo(f"  Default tenant already exists (id={existing.id}).")
                tenant_id = existing.id
            else:
                tenant = Tenant(
                    name="Default Tenant",
                    slug="default",
                    config={},
                )
                session.add(tenant)
                session.flush()
                tenant_id = tenant.id
                click.echo(f"  Created default tenant (id={tenant_id}).")
    except Exception as exc:
        click.echo(f"  Warning: could not create tenant — {exc}", err=True)

    # ------------------------------------------------------------------
    # 3. Generate initial API key
    # ------------------------------------------------------------------
    click.echo("[3/4] Generating initial API key...")
    raw_key: str | None = None
    try:
        from workers.db import get_sync_session
        from api.models.api_key import ApiKey

        raw_key = f"ret_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        if tenant_id is None:
            click.echo("  Skipped — no tenant available.", err=True)
        else:
            with get_sync_session() as session:
                api_key = ApiKey(
                    tenant_id=tenant_id,
                    key_hash=key_hash,
                    name="default-setup-key",
                    permissions={"admin": True},
                )
                session.add(api_key)
                session.flush()
                click.echo(f"  API key created (id={api_key.id}).")
    except Exception as exc:
        click.echo(f"  Warning: could not create API key — {exc}", err=True)
        raw_key = None

    # ------------------------------------------------------------------
    # 4. Initialize plugin registry
    # ------------------------------------------------------------------
    click.echo("[4/4] Initializing plugin registry...")
    try:
        from core.plugin_system.manager import get_plugin_manager

        mgr = get_plugin_manager()
        mgr.initialize()
        plugins = mgr.list_all_plugins()
        click.echo(f"  Discovered {len(plugins)} plugin(s).")
    except Exception as exc:
        click.echo(f"  Warning: plugin initialization failed — {exc}", err=True)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    click.echo("\n" + "=" * 50)
    click.echo("Retrieva setup complete!")
    click.echo("=" * 50)

    if raw_key:
        click.echo(f"\n  Your API key: {raw_key}")
        click.echo("  (save this — it will not be shown again)\n")
    else:
        click.echo("\n  No API key was generated. Run setup again or create one manually.\n")
