import logging
from typing import Optional
from datetime import datetime

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User, SubscriptionTier, SubscriptionStatus

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key

# Price ID to tier mapping
PRICE_TO_TIER = {
    settings.stripe_price_basic: SubscriptionTier.BASIC,
    settings.stripe_price_premium: SubscriptionTier.PREMIUM,
    settings.stripe_price_pro: SubscriptionTier.PRO,
}

TIER_TO_PRICE = {
    SubscriptionTier.BASIC: settings.stripe_price_basic,
    SubscriptionTier.PREMIUM: settings.stripe_price_premium,
    SubscriptionTier.PRO: settings.stripe_price_pro,
}


async def get_or_create_stripe_customer(user: User, db: AsyncSession) -> str:
    """Get or create a Stripe customer for the user."""
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.name,
        metadata={"user_id": user.id},
    )

    user.stripe_customer_id = customer.id
    await db.commit()

    logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
    return customer.id


async def create_checkout_session(
    user: User,
    price_id: str,
    db: AsyncSession,
) -> dict:
    """Create a Stripe checkout session for subscription."""
    customer_id = await get_or_create_stripe_customer(user, db)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.frontend_url}/settings?success=true",
        cancel_url=f"{settings.frontend_url}/settings?canceled=true",
        metadata={"user_id": user.id},
        subscription_data={
            "trial_period_days": 7,  # 7-day trial
            "metadata": {"user_id": user.id},
        },
    )

    logger.info(f"Created checkout session {session.id} for user {user.id}")
    return {"checkout_url": session.url, "session_id": session.id}


async def create_billing_portal_session(user: User, db: AsyncSession) -> dict:
    """Create a Stripe billing portal session."""
    customer_id = await get_or_create_stripe_customer(user, db)

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.frontend_url}/settings",
    )

    return {"portal_url": session.url}


async def handle_subscription_created(subscription: dict, db: AsyncSession) -> None:
    """Handle subscription.created webhook."""
    from app.services.auth import get_user_by_id

    user_id = subscription.get("metadata", {}).get("user_id")
    if not user_id:
        # Try to find user by customer ID
        customer_id = subscription.get("customer")
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
    else:
        user = await get_user_by_id(db, user_id)

    if not user:
        logger.error(f"User not found for subscription {subscription['id']}")
        return

    # Get price and tier
    price_id = subscription["items"]["data"][0]["price"]["id"]
    tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.BASIC)

    # Update user
    user.stripe_subscription_id = subscription["id"]
    user.subscription_tier = tier
    user.subscription_status = SubscriptionStatus.ACTIVE

    if subscription.get("current_period_end"):
        user.subscription_end = datetime.fromtimestamp(subscription["current_period_end"])

    if subscription.get("trial_end"):
        user.trial_end = datetime.fromtimestamp(subscription["trial_end"])
        if subscription.get("status") == "trialing":
            user.subscription_status = SubscriptionStatus.TRIALING

    user.subscription_start = datetime.utcnow()

    await db.commit()
    logger.info(f"Updated user {user.id} subscription to {tier.value}")


async def handle_subscription_updated(subscription: dict, db: AsyncSession) -> None:
    """Handle subscription.updated webhook."""
    from sqlalchemy import select

    subscription_id = subscription["id"]
    result = await db.execute(
        select(User).where(User.stripe_subscription_id == subscription_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"User not found for subscription {subscription_id}")
        return

    # Get price and tier
    price_id = subscription["items"]["data"][0]["price"]["id"]
    tier = PRICE_TO_TIER.get(price_id, user.subscription_tier)

    # Map Stripe status to our status
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "trialing": SubscriptionStatus.TRIALING,
        "unpaid": SubscriptionStatus.INACTIVE,
    }

    user.subscription_tier = tier
    user.subscription_status = status_map.get(
        subscription["status"], SubscriptionStatus.INACTIVE
    )

    if subscription.get("current_period_end"):
        user.subscription_end = datetime.fromtimestamp(subscription["current_period_end"])

    if subscription.get("cancel_at_period_end"):
        user.subscription_status = SubscriptionStatus.CANCELED

    await db.commit()
    logger.info(f"Updated user {user.id} subscription status to {user.subscription_status.value}")


async def handle_subscription_deleted(subscription: dict, db: AsyncSession) -> None:
    """Handle subscription.deleted webhook."""
    from sqlalchemy import select

    subscription_id = subscription["id"]
    result = await db.execute(
        select(User).where(User.stripe_subscription_id == subscription_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.error(f"User not found for subscription {subscription_id}")
        return

    user.subscription_tier = SubscriptionTier.FREE
    user.subscription_status = SubscriptionStatus.INACTIVE
    user.stripe_subscription_id = None

    await db.commit()
    logger.info(f"Canceled subscription for user {user.id}")


async def get_subscription_info(user: User) -> Optional[dict]:
    """Get current subscription info from Stripe."""
    if not user.stripe_subscription_id:
        return None

    try:
        subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
        return {
            "tier": user.subscription_tier.value,
            "status": subscription.get("status"),
            "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]) if subscription.get("current_period_end") else None,
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "trial_end": datetime.fromtimestamp(subscription["trial_end"]) if subscription.get("trial_end") else None,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error fetching subscription: {e}")
        return None


async def cancel_subscription(user: User) -> bool:
    """Cancel subscription at period end."""
    if not user.stripe_subscription_id:
        return False

    try:
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Error canceling subscription: {e}")
        return False


async def sync_subscription_from_stripe(user: User, db: AsyncSession) -> dict:
    """
    Sync user's subscription status from Stripe.
    Useful when webhooks fail or user wants to manually refresh.
    """
    if not user.stripe_customer_id:
        return {
            "synced": False,
            "message": "No Stripe customer ID found",
            "tier": user.subscription_tier.value,
            "status": user.subscription_status.value if user.subscription_status else "inactive",
        }

    try:
        # List all subscriptions for this customer
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",
            limit=1,
        )

        if not subscriptions.data:
            # No subscriptions found - reset to free
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_status = SubscriptionStatus.INACTIVE
            user.stripe_subscription_id = None
            await db.commit()
            return {
                "synced": True,
                "message": "No active subscription found in Stripe",
                "tier": "FREE",
                "status": "inactive",
            }

        # Get the most recent subscription
        subscription = subscriptions.data[0]

        # Update subscription ID if different
        if user.stripe_subscription_id != subscription.get("id"):
            user.stripe_subscription_id = subscription.get("id")

        # Get price and tier
        price_id = subscription["items"]["data"][0]["price"]["id"]
        tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.FREE)

        # Map Stripe status
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "trialing": SubscriptionStatus.TRIALING,
            "unpaid": SubscriptionStatus.INACTIVE,
            "incomplete": SubscriptionStatus.INACTIVE,
            "incomplete_expired": SubscriptionStatus.INACTIVE,
        }

        new_status = status_map.get(subscription.get("status"), SubscriptionStatus.INACTIVE)

        # Handle canceled at period end
        if subscription.get("cancel_at_period_end"):
            new_status = SubscriptionStatus.CANCELED

        # Update user
        user.subscription_tier = tier
        user.subscription_status = new_status

        if subscription.get("current_period_end"):
            user.subscription_end = datetime.fromtimestamp(subscription["current_period_end"])

        if subscription.get("trial_end"):
            user.trial_end = datetime.fromtimestamp(subscription["trial_end"])

        await db.commit()

        logger.info(f"Synced subscription for user {user.id}: {tier.value} ({new_status.value})")

        return {
            "synced": True,
            "message": f"Subscription synced successfully",
            "tier": tier.value,
            "status": new_status.value,
            "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]).isoformat() if subscription.get("current_period_end") else None,
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error syncing subscription from Stripe: {e}")
        return {
            "synced": False,
            "message": f"Stripe error: {str(e)}",
            "tier": user.subscription_tier.value,
            "status": user.subscription_status.value if user.subscription_status else "inactive",
        }
