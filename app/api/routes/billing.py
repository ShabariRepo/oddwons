import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.core.database import get_db
from app.config import get_settings
from app.models.user import User, SubscriptionTier
from app.schemas.user import (
    SubscriptionInfo,
    SubscriptionCreate,
    CheckoutSession,
    BillingPortal,
)
from app.services.auth import get_current_user
from app.services.billing import (
    create_checkout_session,
    create_billing_portal_session,
    get_subscription_info,
    cancel_subscription,
    handle_subscription_created,
    handle_subscription_updated,
    handle_subscription_deleted,
    TIER_TO_PRICE,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionInfo)
async def get_subscription(user: User = Depends(get_current_user)):
    """Get current subscription info."""
    info = await get_subscription_info(user)

    if info:
        return SubscriptionInfo(**info)

    return SubscriptionInfo(
        tier=user.subscription_tier,
        status=user.subscription_status,
        current_period_end=user.subscription_end,
        trial_end=user.trial_end,
    )


@router.post("/checkout", response_model=CheckoutSession)
async def create_checkout(
    data: SubscriptionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a checkout session for subscription."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured",
        )

    result = await create_checkout_session(user, data.price_id, db)
    return CheckoutSession(**result)


@router.post("/checkout/{tier}", response_model=CheckoutSession)
async def create_checkout_by_tier(
    tier: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a checkout session for a specific tier."""
    # Convert lowercase tier to uppercase for enum matching
    tier_enum = SubscriptionTier(tier.upper())
    price_id = TIER_TO_PRICE.get(tier_enum)

    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No price configured for tier: {tier}",
        )

    result = await create_checkout_session(user, price_id, db)
    return CheckoutSession(**result)


@router.post("/portal", response_model=BillingPortal)
async def create_portal(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a billing portal session."""
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No billing account found",
        )

    result = await create_billing_portal_session(user, db)
    return BillingPortal(**result)


@router.post("/cancel")
async def cancel_sub(user: User = Depends(get_current_user)):
    """Cancel subscription at period end."""
    if not user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription",
        )

    success = await cancel_subscription(user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription",
        )

    return {"message": "Subscription will be canceled at period end"}


@router.get("/prices")
async def get_prices():
    """Get available subscription prices."""
    return {
        "prices": [
            {
                "tier": "basic",
                "price_id": settings.stripe_price_basic,
                "amount": 999,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Daily market analysis digest",
                    "Top 5 opportunities",
                    "Email notifications",
                    "Basic pattern alerts",
                ],
            },
            {
                "tier": "premium",
                "price_id": settings.stripe_price_premium,
                "amount": 1999,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Basic",
                    "Real-time opportunity alerts",
                    "Custom alert parameters",
                    "SMS notifications",
                    "Discord/Slack integration",
                    "Historical performance data",
                ],
            },
            {
                "tier": "pro",
                "price_id": settings.stripe_price_pro,
                "amount": 2999,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Premium",
                    "Custom analysis parameters",
                    "Advanced pattern detection",
                    "API access",
                    "Priority support",
                    "Early access to new features",
                ],
            },
        ],
        "publishable_key": settings.stripe_publishable_key,
    }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.stripe_webhook_secret:
        logger.warning("Stripe webhook secret not configured")
        return {"status": "ok"}

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle events
    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    if event_type == "checkout.session.completed":
        # Handle successful checkout - subscription is created separately
        logger.info(f"Checkout completed: {data.get('id')}")
    elif event_type == "customer.subscription.created":
        await handle_subscription_created(data, db)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(data, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(data, db)
    elif event_type == "invoice.payment_failed":
        logger.warning(f"Payment failed for subscription: {data.get('subscription')}")
    elif event_type == "invoice.paid":
        logger.info(f"Invoice paid for subscription: {data.get('subscription')}")

    return {"status": "ok"}
