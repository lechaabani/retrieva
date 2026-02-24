"""Pydantic schemas for billing and subscription endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PlanLimits(BaseModel):
    max_documents: int
    max_queries_per_month: int
    max_collections: int
    max_widgets: int


class PlanInfo(BaseModel):
    name: str
    display_name: str
    price: float
    currency: str = "EUR"
    interval: Optional[str] = None
    features: list[str]
    limits: PlanLimits


class UsageItem(BaseModel):
    used: int
    limit: int
    percentage: float
    label: str


class UsageResponse(BaseModel):
    documents: UsageItem
    queries: UsageItem
    collections: UsageItem
    widgets: UsageItem


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    usage: UsageResponse
    limits: PlanLimits

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    plan: str = Field(..., pattern=r"^(pro|enterprise)$")


class CheckoutResponse(BaseModel):
    checkout_url: str


class BillingPortalResponse(BaseModel):
    portal_url: str
