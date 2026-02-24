"""Billing and subscription management endpoints."""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.tenant import Tenant
from api.models.subscription import Subscription
from api.models.document import Document
from api.models.collection import Collection
from api.models.query_log import QueryLog
from api.models.widget_config import WidgetConfig
from api.schemas.billing import (
    BillingPortalResponse,
    CheckoutRequest,
    CheckoutResponse,
    PlanInfo,
    PlanLimits,
    SubscriptionResponse,
    UsageItem,
    UsageResponse,
)

logger = logging.getLogger("retrieva.billing")

router = APIRouter(prefix="/billing", tags=["Billing"])

# ---------------------------------------------------------------------------
# Plan definitions
# ---------------------------------------------------------------------------

PLANS: dict[str, PlanInfo] = {
    "community": PlanInfo(
        name="community",
        display_name="Community",
        price=0,
        currency="EUR",
        interval=None,
        features=[
            "100 documents",
            "1 000 requetes / mois",
            "3 collections",
            "Support communautaire",
            "API REST complète",
        ],
        limits=PlanLimits(
            max_documents=100,
            max_queries_per_month=1000,
            max_collections=3,
            max_widgets=0,
        ),
    ),
    "pro": PlanInfo(
        name="pro",
        display_name="Pro",
        price=29,
        currency="EUR",
        interval="month",
        features=[
            "10 000 documents",
            "50 000 requetes / mois",
            "50 collections",
            "10 widgets",
            "Support prioritaire",
            "API REST complète",
            "Connecteurs avances",
            "Analytics avances",
        ],
        limits=PlanLimits(
            max_documents=10000,
            max_queries_per_month=50000,
            max_collections=50,
            max_widgets=10,
        ),
    ),
    "enterprise": PlanInfo(
        name="enterprise",
        display_name="Enterprise",
        price=-1,
        currency="EUR",
        interval="month",
        features=[
            "Documents illimites",
            "Requetes illimitees",
            "Collections illimitees",
            "Widgets illimites",
            "Support dedie",
            "SLA garanti",
            "SSO / SAML",
            "Deploiement on-premise",
            "API REST complète",
        ],
        limits=PlanLimits(
            max_documents=-1,
            max_queries_per_month=-1,
            max_collections=-1,
            max_widgets=-1,
        ),
    ),
}

STRIPE_PRICE_MAP = {
    "pro": os.getenv("STRIPE_PRICE_PRO", ""),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", ""),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plan_limits(plan: str) -> PlanLimits:
    """Return the limits for a given plan name."""
    if plan in PLANS:
        return PLANS[plan].limits
    return PLANS["community"].limits


async def _get_or_create_subscription(
    tenant: Tenant, db: AsyncSession
) -> Subscription:
    """Fetch the subscription for a tenant, creating a community one if missing."""
    stmt = select(Subscription).where(Subscription.tenant_id == tenant.id)
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = Subscription(
            tenant_id=tenant.id,
            plan="community",
            status="active",
            max_documents=100,
            max_queries_per_month=1000,
            max_collections=3,
            max_widgets=0,
        )
        db.add(sub)
        await db.flush()
    return sub


async def _count_usage(tenant_id, db: AsyncSession) -> dict:
    """Count actual resource usage for a tenant."""
    # Documents count via collections
    doc_stmt = (
        select(func.count(Document.id))
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant_id)
    )
    doc_result = await db.execute(doc_stmt)
    documents_used = doc_result.scalar() or 0

    # Collections count
    col_stmt = select(func.count(Collection.id)).where(
        Collection.tenant_id == tenant_id
    )
    col_result = await db.execute(col_stmt)
    collections_used = col_result.scalar() or 0

    # Widgets count
    wid_stmt = select(func.count(WidgetConfig.id)).where(
        WidgetConfig.tenant_id == tenant_id
    )
    wid_result = await db.execute(wid_stmt)
    widgets_used = wid_result.scalar() or 0

    # Queries this month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    q_stmt = (
        select(func.count(QueryLog.id))
        .where(QueryLog.tenant_id == tenant_id)
        .where(QueryLog.created_at >= month_start)
    )
    q_result = await db.execute(q_stmt)
    queries_used = q_result.scalar() or 0

    return {
        "documents_used": documents_used,
        "collections_used": collections_used,
        "widgets_used": widgets_used,
        "queries_used": queries_used,
    }


def _calc_percentage(used: int, limit: int) -> float:
    """Calculate usage percentage. Returns 0.0 for unlimited (-1)."""
    if limit <= 0:
        return 0.0
    return round(min(used / limit * 100, 100.0), 1)


def _build_usage_response(usage: dict, limits: PlanLimits) -> UsageResponse:
    return UsageResponse(
        documents=UsageItem(
            used=usage["documents_used"],
            limit=limits.max_documents,
            percentage=_calc_percentage(usage["documents_used"], limits.max_documents),
            label="Documents",
        ),
        queries=UsageItem(
            used=usage["queries_used"],
            limit=limits.max_queries_per_month,
            percentage=_calc_percentage(
                usage["queries_used"], limits.max_queries_per_month
            ),
            label="Requetes ce mois",
        ),
        collections=UsageItem(
            used=usage["collections_used"],
            limit=limits.max_collections,
            percentage=_calc_percentage(
                usage["collections_used"], limits.max_collections
            ),
            label="Collections",
        ),
        widgets=UsageItem(
            used=usage["widgets_used"],
            limit=limits.max_widgets,
            percentage=_calc_percentage(usage["widgets_used"], limits.max_widgets),
            label="Widgets",
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/plans", response_model=list[PlanInfo])
async def list_plans(
    _tenant: Tenant = Depends(get_current_tenant),
):
    """Return available plans with features and pricing."""
    return list(PLANS.values())


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Return the current tenant's subscription and usage stats."""
    sub = await _get_or_create_subscription(tenant, db)
    usage = await _count_usage(tenant.id, db)
    limits = _plan_limits(sub.plan)
    return SubscriptionResponse(
        plan=sub.plan,
        status=sub.status,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        usage=_build_usage_response(usage, limits),
        limits=limits,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session for upgrading to a paid plan."""
    stripe_secret = os.getenv("STRIPE_SECRET_KEY")

    if not stripe_secret:
        # Development mode: return mock checkout URL
        logger.warning("STRIPE_SECRET_KEY not set -- returning mock checkout URL")
        return CheckoutResponse(
            checkout_url=f"https://checkout.stripe.com/mock?plan={body.plan}"
        )

    try:
        import stripe

        stripe.api_key = stripe_secret
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe SDK not installed. Run: pip install stripe",
        )

    sub = await _get_or_create_subscription(tenant, db)

    # Create or retrieve Stripe customer
    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(
            name=tenant.name,
            metadata={"tenant_id": str(tenant.id)},
        )
        sub.stripe_customer_id = customer.id
        await db.flush()

    price_id = STRIPE_PRICE_MAP.get(body.plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No Stripe price configured for plan '{body.plan}'. Set STRIPE_PRICE_{body.plan.upper()} env var.",
        )

    dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:3000")
    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{dashboard_url}/settings/billing?success=true",
        cancel_url=f"{dashboard_url}/settings/billing?canceled=true",
        metadata={"tenant_id": str(tenant.id)},
    )

    return CheckoutResponse(checkout_url=session.url)


@router.post("/portal", response_model=BillingPortalResponse)
async def create_billing_portal(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe billing portal session for managing the subscription."""
    stripe_secret = os.getenv("STRIPE_SECRET_KEY")

    if not stripe_secret:
        logger.warning("STRIPE_SECRET_KEY not set -- returning mock portal URL")
        return BillingPortalResponse(
            portal_url="https://billing.stripe.com/mock/portal"
        )

    try:
        import stripe

        stripe.api_key = stripe_secret
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe SDK not installed.",
        )

    sub = await _get_or_create_subscription(tenant, db)
    if not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer linked to this tenant. Subscribe to a plan first.",
        )

    dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:3000")
    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{dashboard_url}/settings/billing",
    )

    return BillingPortalResponse(portal_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events. No auth -- Stripe calls this directly."""
    stripe_secret = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    payload = await request.body()

    if stripe_secret:
        try:
            import stripe

            stripe.api_key = stripe_secret
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe SDK not installed.",
            )

        if webhook_secret:
            sig_header = request.headers.get("stripe-signature", "")
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except stripe.error.SignatureVerificationError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook signature.",
                )
        else:
            # Development mode: parse event without signature verification
            import json

            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
    else:
        # No Stripe key -- development mode, parse raw JSON
        import json

        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload.",
            )
        logger.info("Received mock webhook event: %s", event_data.get("type"))
        return {"status": "ok", "mode": "development"}

    # Process the event
    event_type = event.type
    logger.info("Processing Stripe webhook: %s", event_type)

    async with AsyncSession(bind=db_engine()) as db:
        try:
            if event_type == "checkout.session.completed":
                await _handle_checkout_completed(event.data.object, db)
            elif event_type == "customer.subscription.updated":
                await _handle_subscription_updated(event.data.object, db)
            elif event_type == "customer.subscription.deleted":
                await _handle_subscription_deleted(event.data.object, db)
            elif event_type == "invoice.payment_failed":
                await _handle_payment_failed(event.data.object, db)
            else:
                logger.debug("Unhandled webhook event type: %s", event_type)

            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Error processing webhook event %s", event_type)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook processing error.",
            )

    return {"status": "ok"}


def db_engine():
    """Lazy import to avoid circular dependencies."""
    from api.database import engine

    return engine


def _plan_from_price(price_id: str) -> str:
    """Resolve a Stripe price ID to a plan name."""
    for plan_name, pid in STRIPE_PRICE_MAP.items():
        if pid == price_id:
            return plan_name
    return "pro"  # default fallback


def _apply_plan_limits(sub: Subscription, plan: str) -> None:
    """Set subscription limits based on plan."""
    limits = _plan_limits(plan)
    sub.plan = plan
    sub.max_documents = limits.max_documents
    sub.max_queries_per_month = limits.max_queries_per_month
    sub.max_collections = limits.max_collections
    sub.max_widgets = limits.max_widgets


async def _handle_checkout_completed(session_obj, db: AsyncSession) -> None:
    """Handle checkout.session.completed: activate the new subscription."""
    customer_id = session_obj.customer
    subscription_id = session_obj.subscription

    stmt = select(Subscription).where(
        Subscription.stripe_customer_id == customer_id
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        logger.warning("No subscription found for customer %s", customer_id)
        return

    sub.stripe_subscription_id = subscription_id
    sub.status = "active"

    # Determine plan from the subscription
    try:
        import stripe

        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        if stripe_sub.items.data:
            price_id = stripe_sub.items.data[0].price.id
            plan = _plan_from_price(price_id)
            _apply_plan_limits(sub, plan)
            sub.current_period_start = datetime.fromtimestamp(
                stripe_sub.current_period_start, tz=timezone.utc
            )
            sub.current_period_end = datetime.fromtimestamp(
                stripe_sub.current_period_end, tz=timezone.utc
            )
    except Exception:
        logger.exception("Error fetching subscription details")
        _apply_plan_limits(sub, "pro")


async def _handle_subscription_updated(sub_obj, db: AsyncSession) -> None:
    """Handle customer.subscription.updated: sync plan and status."""
    customer_id = sub_obj.customer

    stmt = select(Subscription).where(
        Subscription.stripe_customer_id == customer_id
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        logger.warning("No subscription found for customer %s", customer_id)
        return

    sub.status = sub_obj.status
    sub.cancel_at_period_end = getattr(sub_obj, "cancel_at_period_end", False)

    if hasattr(sub_obj, "current_period_start") and sub_obj.current_period_start:
        sub.current_period_start = datetime.fromtimestamp(
            sub_obj.current_period_start, tz=timezone.utc
        )
    if hasattr(sub_obj, "current_period_end") and sub_obj.current_period_end:
        sub.current_period_end = datetime.fromtimestamp(
            sub_obj.current_period_end, tz=timezone.utc
        )

    # Update plan if price changed
    if sub_obj.items and sub_obj.items.data:
        price_id = sub_obj.items.data[0].price.id
        plan = _plan_from_price(price_id)
        _apply_plan_limits(sub, plan)


async def _handle_subscription_deleted(sub_obj, db: AsyncSession) -> None:
    """Handle customer.subscription.deleted: revert to community plan."""
    customer_id = sub_obj.customer

    stmt = select(Subscription).where(
        Subscription.stripe_customer_id == customer_id
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        return

    sub.status = "canceled"
    _apply_plan_limits(sub, "community")
    sub.stripe_subscription_id = None
    sub.current_period_end = None
    sub.cancel_at_period_end = False


async def _handle_payment_failed(invoice_obj, db: AsyncSession) -> None:
    """Handle invoice.payment_failed: mark subscription as past_due."""
    customer_id = invoice_obj.customer

    stmt = select(Subscription).where(
        Subscription.stripe_customer_id == customer_id
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        return

    sub.status = "past_due"


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Return current usage vs limits with percentages."""
    sub = await _get_or_create_subscription(tenant, db)
    usage = await _count_usage(tenant.id, db)
    limits = _plan_limits(sub.plan)
    return _build_usage_response(usage, limits)
