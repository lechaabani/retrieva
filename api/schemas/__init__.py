"""Pydantic schemas for request/response validation."""

from api.schemas.query import (
    QueryRequest,
    QueryOptions,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    Source,
    SearchResult,
)
from api.schemas.document import DocumentCreate, DocumentResponse, DocumentList
from api.schemas.collection import CollectionCreate, CollectionResponse, CollectionList
from api.schemas.ingest import IngestResponse, IngestTextRequest
from api.schemas.auth import (
    ApiKeyCreate,
    ApiKeyResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from api.schemas.admin import AnalyticsResponse, TenantConfig, WebhookConfig
from api.schemas.plugin import (
    PluginInfo,
    PluginListResponse,
    PluginInstallRequest,
    PluginConfigRequest,
)
from api.schemas.template import TemplateInfo, TemplateDownloadRequest
from api.schemas.billing import (
    PlanInfo as BillingPlanInfo,
    PlanLimits,
    SubscriptionResponse,
    UsageResponse as BillingUsageResponse,
    CheckoutRequest,
    CheckoutResponse,
    BillingPortalResponse,
)

__all__ = [
    "QueryRequest",
    "QueryOptions",
    "QueryResponse",
    "SearchRequest",
    "SearchResponse",
    "Source",
    "SearchResult",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentList",
    "CollectionCreate",
    "CollectionResponse",
    "CollectionList",
    "IngestResponse",
    "IngestTextRequest",
    "ApiKeyCreate",
    "ApiKeyResponse",
    "TokenResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "AnalyticsResponse",
    "TenantConfig",
    "WebhookConfig",
    "PluginInfo",
    "PluginListResponse",
    "PluginInstallRequest",
    "PluginConfigRequest",
    "TemplateInfo",
    "TemplateDownloadRequest",
    "BillingPlanInfo",
    "PlanLimits",
    "SubscriptionResponse",
    "BillingUsageResponse",
    "CheckoutRequest",
    "CheckoutResponse",
    "BillingPortalResponse",
]
