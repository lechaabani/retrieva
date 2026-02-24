"""Template management endpoints: list, detail, download, and preview."""

import io
import json
import logging
import mimetypes
import os
import re
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse

from api.auth.api_keys import get_current_tenant
from api.models.tenant import Tenant
from api.schemas.template import TemplateDownloadRequest, TemplateInfo

logger = logging.getLogger("retrieva.api.templates")

router = APIRouter(prefix="/templates", tags=["Templates"])

# Resolve the templates directory relative to the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = _PROJECT_ROOT / "templates"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_manifest(template_dir: Path) -> dict:
    """Read manifest.json from a template directory, or synthesise metadata."""
    manifest_path = template_dir / "manifest.json"
    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback: generate metadata from directory name
    name = template_dir.name
    title = name.replace("-", " ").title()
    files = [p.name for p in template_dir.iterdir() if p.is_file() and p.name != "manifest.json"]
    return {
        "name": name,
        "title": title,
        "description": "",
        "type": name.split("-")[0] if "-" in name else name,
        "files": sorted(files),
    }


def _get_template_dir(name: str) -> Path:
    """Resolve a template directory by name, with path-traversal protection."""
    # Reject any path component tricks
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template name.",
        )

    template_dir = TEMPLATES_DIR / name
    # Ensure resolved path is still inside TEMPLATES_DIR
    try:
        template_dir.resolve().relative_to(TEMPLATES_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template name.",
        )

    if not template_dir.is_dir():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{name}' not found.",
        )
    return template_dir


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[TemplateInfo],
    summary="List Templates",
    description="List all available standalone HTML templates.",
)
async def list_templates(
    tenant: Tenant = Depends(get_current_tenant),
) -> list[TemplateInfo]:
    """Scan the templates/ directory and return metadata for each template."""
    if not TEMPLATES_DIR.is_dir():
        return []

    templates: list[TemplateInfo] = []
    for entry in sorted(TEMPLATES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        manifest = _read_manifest(entry)
        templates.append(
            TemplateInfo(
                name=manifest.get("name", entry.name),
                title=manifest.get("title", entry.name.replace("-", " ").title()),
                description=manifest.get("description", ""),
                template_type=manifest.get("type", ""),
                files=manifest.get("files", []),
            )
        )
    return templates


@router.get(
    "/{name}",
    response_model=TemplateInfo,
    summary="Get Template Details",
    description="Return metadata and file list for a specific template.",
)
async def get_template(
    name: str,
    tenant: Tenant = Depends(get_current_tenant),
) -> TemplateInfo:
    """Return detailed info for a single template."""
    template_dir = _get_template_dir(name)
    manifest = _read_manifest(template_dir)
    return TemplateInfo(
        name=manifest.get("name", name),
        title=manifest.get("title", name.replace("-", " ").title()),
        description=manifest.get("description", ""),
        template_type=manifest.get("type", ""),
        files=manifest.get("files", []),
    )


@router.post(
    "/{name}/download",
    summary="Download Configured Template",
    description="Generate a zip archive of the template with configuration placeholders replaced.",
)
async def download_template(
    name: str,
    body: TemplateDownloadRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> StreamingResponse:
    """Build an in-memory zip with config placeholders replaced, and stream it."""
    template_dir = _get_template_dir(name)
    manifest = _read_manifest(template_dir)
    files = manifest.get("files", [])

    if not files:
        # Fallback: include all non-manifest files
        files = [
            p.name
            for p in template_dir.iterdir()
            if p.is_file() and p.name != "manifest.json"
        ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            file_path = template_dir / filename
            if not file_path.is_file():
                continue

            content = file_path.read_text(encoding="utf-8")

            # ---- Replace config placeholders in app.js ----
            if filename.endswith(".js"):
                content = _replace_js_config(content, body)

            # ---- Replace CSS variable defaults in styles.css ----
            if filename.endswith(".css"):
                content = _replace_css_config(content, body)

            zf.writestr(f"{name}/{filename}", content)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{name}.zip"',
        },
    )


@router.get(
    "/{name}/preview/{filename:path}",
    summary="Preview Template File",
    description="Serve a raw template file for iframe preview. No authentication required.",
)
async def preview_template_file(
    name: str,
    filename: str,
) -> Response:
    """Serve a template file with the correct content-type. No auth required."""
    template_dir = _get_template_dir(name)

    # Path-traversal protection for filename
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    file_path = (template_dir / filename).resolve()
    # Ensure the resolved path is within the template directory
    try:
        file_path.relative_to(template_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found in template '{name}'.",
        )

    content = file_path.read_bytes()
    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = "application/octet-stream"

    return Response(content=content, media_type=content_type)


# ---------------------------------------------------------------------------
# Config replacement helpers
# ---------------------------------------------------------------------------


def _replace_js_config(content: str, body: TemplateDownloadRequest) -> str:
    """Replace RETRIEVA_CONFIG placeholder values in JavaScript files."""
    # The templates use camelCase keys inside RETRIEVA_CONFIG:
    #   apiUrl: "http://localhost:8000",
    #   apiKey: "YOUR_PUBLIC_API_KEY",
    #   widgetId: "YOUR_WIDGET_ID",
    replacements = {
        "apiUrl": body.api_url,
        "apiKey": body.api_key,
        "widgetId": body.widget_id,
    }

    for key, value in replacements.items():
        # Match patterns like:  apiUrl: "...",  or  apiUrl = "..."
        pattern = rf'({key}\s*[:=]\s*)["\'].*?["\']'
        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
        content = re.sub(pattern, rf'\1"{escaped_value}"', content)

    # Replace arbitrary config keys if provided in body.config
    for key, value in body.config.items():
        safe_key = re.escape(key)
        pattern = rf'({safe_key}\s*[:=]\s*)["\'].*?["\']'
        if isinstance(value, str):
            escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
            content = re.sub(pattern, rf'\1"{escaped_value}"', content)

    return content


def _replace_css_config(content: str, body: TemplateDownloadRequest) -> str:
    """Replace CSS custom property defaults with provided config values."""
    config = body.config
    if not config:
        return content

    # Replace CSS variable defaults.  Templates use e.g.:  --primary: #4F46E5;
    color_mappings = {
        "primary_color": "--primary",
        "primary_hover": "--primary-hover",
        "background_color": "--bg",
        "text_color": "--text",
        "border_color": "--border",
    }

    for config_key, css_var in color_mappings.items():
        if config_key in config:
            value = config[config_key]
            escaped_var = re.escape(css_var)
            pattern = rf'({escaped_var}\s*:\s*)([^;]+)(;)'
            content = re.sub(pattern, rf'\g<1>{value}\3', content)

    return content
