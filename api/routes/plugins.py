"""Plugin management endpoints: list, enable, disable, install, uninstall, configure."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.auth.api_keys import get_current_tenant
from api.models.tenant import Tenant
from api.schemas.plugin import (
    PluginConfigRequest,
    PluginInfo,
    PluginInstallRequest,
    PluginListResponse,
)

router = APIRouter(tags=["Plugins"])


def _get_plugin_manager(request: Request) -> Any:
    """Retrieve the plugin manager from app state."""
    pm = getattr(request.app.state, "plugin_manager", None)
    if pm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Plugin manager is not available.",
        )
    return pm


# ---------------------------------------------------------------------------
# List plugins
# ---------------------------------------------------------------------------

@router.get(
    "/plugins",
    response_model=PluginListResponse,
    summary="List Plugins",
    description="List all registered plugins and their statuses.",
)
async def list_plugins(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> PluginListResponse:
    """Return metadata for every registered plugin."""
    pm = _get_plugin_manager(request)
    plugins = pm.list_all_plugins()
    items = [PluginInfo.model_validate(p) for p in plugins]
    return PluginListResponse(plugins=items, total=len(items))


# ---------------------------------------------------------------------------
# Single plugin info
# ---------------------------------------------------------------------------

@router.get(
    "/plugins/{name}",
    response_model=PluginInfo,
    summary="Get Plugin",
    description="Retrieve detailed information about a single plugin.",
)
async def get_plugin(
    name: str,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> PluginInfo:
    """Return metadata for a specific plugin by name."""
    pm = _get_plugin_manager(request)
    plugin = pm.get_plugin(name)
    if plugin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found.",
        )
    return PluginInfo.model_validate(plugin)


# ---------------------------------------------------------------------------
# Enable / Disable
# ---------------------------------------------------------------------------

@router.post(
    "/plugins/{name}/enable",
    response_model=PluginInfo,
    summary="Enable Plugin",
    description="Enable a previously disabled plugin.",
)
async def enable_plugin(
    name: str,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> PluginInfo:
    """Enable the named plugin."""
    pm = _get_plugin_manager(request)
    try:
        plugin = pm.enable_plugin(name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found.",
        )
    return PluginInfo.model_validate(plugin)


@router.post(
    "/plugins/{name}/disable",
    response_model=PluginInfo,
    summary="Disable Plugin",
    description="Disable an active plugin.",
)
async def disable_plugin(
    name: str,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> PluginInfo:
    """Disable the named plugin."""
    pm = _get_plugin_manager(request)
    try:
        plugin = pm.disable_plugin(name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found.",
        )
    return PluginInfo.model_validate(plugin)


# ---------------------------------------------------------------------------
# Install / Uninstall
# ---------------------------------------------------------------------------

@router.post(
    "/plugins/install",
    response_model=PluginInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Install Plugin",
    description="Install a plugin from a local path, Git URL, or PyPI package.",
)
async def install_plugin(
    payload: PluginInstallRequest,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> PluginInfo:
    """Install a plugin from the given source."""
    pm = _get_plugin_manager(request)
    try:
        plugin = pm.install_plugin(payload.source)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to install plugin: {exc}",
        )
    return PluginInfo.model_validate(plugin)


@router.delete(
    "/plugins/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Uninstall Plugin",
    description="Uninstall a non-bundled plugin.",
)
async def uninstall_plugin(
    name: str,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> None:
    """Remove the named plugin."""
    pm = _get_plugin_manager(request)
    try:
        pm.uninstall_plugin(name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Marketplace
# ---------------------------------------------------------------------------

@router.get(
    "/plugins/marketplace",
    summary="Plugin Marketplace",
    description="Return the list of available plugins from the marketplace catalog.",
)
async def get_marketplace(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    """Read and return the marketplace catalog."""
    marketplace_path = Path(__file__).resolve().parent.parent.parent / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        return {"plugins": [], "total": 0}
    try:
        data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read marketplace catalog: {exc}",
        )
    return data


# ---------------------------------------------------------------------------
# Plugin configuration
# ---------------------------------------------------------------------------

@router.put(
    "/plugins/{name}/config",
    response_model=PluginInfo,
    summary="Update Plugin Config",
    description="Update the runtime configuration for a specific plugin.",
)
async def update_plugin_config(
    name: str,
    payload: PluginConfigRequest,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
) -> PluginInfo:
    """Merge the provided config into the plugin's current configuration."""
    pm = _get_plugin_manager(request)
    try:
        plugin = pm.configure_plugin(name, payload.config)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found.",
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid configuration: {exc}",
        )
    return PluginInfo.model_validate(plugin)
