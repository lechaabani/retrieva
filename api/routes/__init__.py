"""API route modules."""

from api.routes.query import router as query_router
from api.routes.ingest import router as ingest_router
from api.routes.documents import router as documents_router
from api.routes.collections import router as collections_router
from api.routes.admin import router as admin_router
from api.routes.plugins import router as plugins_router
from api.routes.sources import router as sources_router
from api.routes.setup import router as setup_router
from api.routes.widget import router as widget_router
from api.routes.widget_admin import router as widget_admin_router
from api.routes.templates import router as templates_router
from api.routes.eval import router as eval_router
from api.routes.activity import router as activity_router
from api.routes.compare import router as compare_router
from api.routes.suggestions import router as suggestions_router
from api.routes.analytics_dashboard import router as analytics_dashboard_router
from api.routes.billing import router as billing_router

__all__ = [
    "query_router",
    "ingest_router",
    "documents_router",
    "collections_router",
    "admin_router",
    "plugins_router",
    "sources_router",
    "setup_router",
    "widget_router",
    "widget_admin_router",
    "templates_router",
    "eval_router",
    "activity_router",
    "compare_router",
    "suggestions_router",
    "analytics_dashboard_router",
    "billing_router",
]
