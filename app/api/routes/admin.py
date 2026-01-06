from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timedelta
import stripe

from app.core.database import get_db
from app.models.user import User, SubscriptionTier, SubscriptionStatus
from app.models.ai_insight import AIInsight
from app.models.market import Market
from app.services.auth import require_admin
from app.services.billing import PRICE_TO_TIER
from app.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


# ============ USER MANAGEMENT ============

@router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with search and filter."""
    query = select(User)

    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") |
            User.name.ilike(f"%{search}%")
        )

    if tier:
        query = query.where(User.subscription_tier == SubscriptionTier(tier.upper()))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.order_by(desc(User.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "subscription_tier": u.subscription_tier.value if u.subscription_tier else "free",
                "subscription_status": u.subscription_status.value if u.subscription_status else None,
                "stripe_customer_id": u.stripe_customer_id,
                "trial_end": u.trial_end.isoformat() if u.trial_end else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "is_admin": u.is_admin,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user info."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get Stripe subscription details if exists
    stripe_sub = None
    if user.stripe_subscription_id:
        try:
            stripe_sub = stripe.Subscription.retrieve(user.stripe_subscription_id)
        except:
            pass

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "subscription_tier": user.subscription_tier.value if user.subscription_tier else "free",
            "subscription_status": user.subscription_status.value if user.subscription_status else None,
            "stripe_customer_id": user.stripe_customer_id,
            "stripe_subscription_id": user.stripe_subscription_id,
            "trial_end": user.trial_end.isoformat() if user.trial_end else None,
            "subscription_end": user.subscription_end.isoformat() if user.subscription_end else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_admin": user.is_admin,
        },
        "stripe_subscription": {
            "id": stripe_sub.id,
            "status": stripe_sub.status,
            "current_period_end": stripe_sub.current_period_end,
            "trial_end": stripe_sub.trial_end,
            "cancel_at_period_end": stripe_sub.cancel_at_period_end,
        } if stripe_sub else None,
    }


@router.post("/users/{user_id}/sync-subscription")
async def sync_user_subscription(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Sync user's subscription from Stripe."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.stripe_customer_id:
        return {"message": "No Stripe customer ID", "synced": False}

    try:
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",
            limit=1,
        )

        if not subscriptions.data:
            user.subscription_tier = SubscriptionTier.FREE
            user.subscription_status = SubscriptionStatus.INACTIVE
            user.stripe_subscription_id = None
            await db.commit()
            return {"message": "No subscription found - set to FREE", "synced": True, "tier": "free"}

        sub = subscriptions.data[0]
        price_id = sub["items"]["data"][0]["price"]["id"]
        tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.BASIC)

        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
        }

        user.subscription_tier = tier
        user.subscription_status = status_map.get(sub["status"], SubscriptionStatus.INACTIVE)
        user.stripe_subscription_id = sub["id"]

        if sub.get("current_period_end"):
            user.subscription_end = datetime.fromtimestamp(sub["current_period_end"])
        if sub.get("trial_end"):
            user.trial_end = datetime.fromtimestamp(sub["trial_end"])

        await db.commit()

        return {
            "message": "Subscription synced",
            "synced": True,
            "tier": tier.value,
            "status": sub["status"],
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/change-tier")
async def change_user_tier(
    user_id: str,
    tier: str = Query(..., description="new tier: free, basic, premium, pro"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually change user's tier (for comp accounts, testing, etc)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_tier = user.subscription_tier.value if user.subscription_tier else "free"
    user.subscription_tier = SubscriptionTier(tier.upper())

    if tier.upper() != "FREE":
        user.subscription_status = SubscriptionStatus.ACTIVE

    await db.commit()

    return {
        "message": f"Tier changed from {old_tier} to {tier}",
        "user_id": user_id,
        "old_tier": old_tier,
        "new_tier": tier,
    }


@router.post("/users/{user_id}/grant-trial")
async def grant_trial(
    user_id: str,
    days: int = Query(7, ge=1, le=90),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Grant user a trial period."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.trial_end = datetime.utcnow() + timedelta(days=days)
    user.subscription_status = SubscriptionStatus.TRIALING

    if user.subscription_tier == SubscriptionTier.FREE:
        user.subscription_tier = SubscriptionTier.BASIC

    await db.commit()

    return {
        "message": f"Granted {days} day trial",
        "trial_end": user.trial_end.isoformat(),
    }


# ============ STATS & ANALYTICS ============

@router.get("/stats")
async def get_admin_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard stats."""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # User counts
    total_users = await db.scalar(select(func.count()).select_from(User))
    new_users_24h = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at > day_ago)
    )
    new_users_7d = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at > week_ago)
    )

    # Tier distribution
    tier_counts = {}
    for tier in SubscriptionTier:
        count = await db.scalar(
            select(func.count()).select_from(User).where(User.subscription_tier == tier)
        )
        tier_counts[tier.value.lower()] = count or 0

    # Trialing users
    trialing = await db.scalar(
        select(func.count()).select_from(User)
        .where(User.subscription_status == SubscriptionStatus.TRIALING)
    )

    # Content stats
    total_markets = await db.scalar(select(func.count()).select_from(Market))
    total_insights = await db.scalar(
        select(func.count()).select_from(AIInsight).where(AIInsight.status == "active")
    )

    # Revenue estimate (paid users * avg price)
    paid_users = (tier_counts.get("basic", 0) +
                  tier_counts.get("premium", 0) +
                  tier_counts.get("pro", 0))
    estimated_mrr = (
        tier_counts.get("basic", 0) * 9.99 +
        tier_counts.get("premium", 0) * 19.99 +
        tier_counts.get("pro", 0) * 29.99
    )

    return {
        "users": {
            "total": total_users,
            "new_24h": new_users_24h,
            "new_7d": new_users_7d,
            "trialing": trialing,
        },
        "tiers": tier_counts,
        "revenue": {
            "paid_users": paid_users,
            "estimated_mrr": round(estimated_mrr, 2),
        },
        "content": {
            "total_markets": total_markets,
            "active_insights": total_insights,
        },
    }


@router.get("/webhook-logs")
async def get_webhook_logs(
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
):
    """Get recent Stripe webhook events."""
    try:
        events = stripe.Event.list(limit=limit)
        return {
            "events": [
                {
                    "id": e.id,
                    "type": e.type,
                    "created": datetime.fromtimestamp(e.created).isoformat(),
                    "data": {
                        "object_id": e.data.object.get("id") if hasattr(e.data, "object") else None,
                    },
                }
                for e in events.data
            ]
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ CONTENT MANAGEMENT ============

@router.post("/insights/regenerate")
async def regenerate_insights(
    category: Optional[str] = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI insight regeneration."""
    from app.services.patterns.engine import pattern_engine

    try:
        results = await pattern_engine.run_full_analysis(with_ai=True)
        return {
            "message": "Insights regenerated",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/insights/clear-stale")
async def clear_stale_insights(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete expired/stale AI insights."""
    result = await db.execute(
        select(func.count()).select_from(AIInsight)
        .where(AIInsight.expires_at < datetime.utcnow())
    )
    stale_count = result.scalar() or 0

    await db.execute(
        AIInsight.__table__.delete().where(AIInsight.expires_at < datetime.utcnow())
    )
    await db.commit()

    return {"message": f"Deleted {stale_count} stale insights"}


# ============ SYSTEM HEALTH ============

@router.get("/health")
async def system_health(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Check system health."""
    health = {
        "database": "unknown",
        "redis": "unknown",
        "stripe": "unknown",
    }

    # Database
    try:
        await db.execute(select(1))
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"error: {str(e)}"

    # Redis
    try:
        from app.core.database import get_redis
        r = await get_redis()
        await r.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"

    # Stripe
    try:
        stripe.Account.retrieve()
        health["stripe"] = "healthy"
    except Exception as e:
        health["stripe"] = f"error: {str(e)}"

    return health
