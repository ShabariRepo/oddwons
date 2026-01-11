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
from app.models.x_post import XPost, XPostType, XPostStatus, XBotSettings
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
            "id": stripe_sub.get("id"),
            "status": stripe_sub.get("status"),
            "current_period_end": stripe_sub.get("current_period_end"),
            "trial_end": stripe_sub.get("trial_end"),
            "cancel_at_period_end": stripe_sub.get("cancel_at_period_end", False),
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


# ============ STRIPE SUBSCRIPTION MANAGEMENT ============

@router.get("/users/{user_id}/stripe-subscriptions")
async def list_user_stripe_subscriptions(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List ALL subscriptions for a user in Stripe.
    Useful for finding duplicates.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.stripe_customer_id:
        return {"subscriptions": [], "message": "No Stripe customer ID"}

    try:
        # Get ALL subscriptions (not just active)
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",  # active, trialing, canceled, etc.
            limit=10,
        )

        return {
            "customer_id": user.stripe_customer_id,
            "subscriptions": [
                {
                    "id": sub.get("id"),
                    "status": sub.get("status"),
                    "price_id": sub["items"]["data"][0]["price"]["id"],
                    "current_period_end": datetime.fromtimestamp(sub["current_period_end"]).isoformat() if sub.get("current_period_end") else None,
                    "trial_end": datetime.fromtimestamp(sub["trial_end"]).isoformat() if sub.get("trial_end") else None,
                    "cancel_at_period_end": sub.get("cancel_at_period_end", False),
                    "created": datetime.fromtimestamp(sub["created"]).isoformat() if sub.get("created") else None,
                }
                for sub in subscriptions.data
            ],
            "count": len(subscriptions.data),
            "has_duplicates": len([s for s in subscriptions.data if s.get("status") in ["active", "trialing"]]) > 1,
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/cancel-stripe-subscription/{subscription_id}")
async def cancel_stripe_subscription(
    user_id: str,
    subscription_id: str,
    immediately: bool = Query(False, description="Cancel immediately vs at period end"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a specific Stripe subscription.
    Use this to clean up duplicates.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if immediately:
            # Cancel immediately - no more access
            canceled_sub = stripe.Subscription.cancel(subscription_id)
            message = "Subscription canceled immediately"
        else:
            # Cancel at period end - user keeps access until then
            canceled_sub = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            message = "Subscription will cancel at period end"

        # If this was the user's active subscription, clear it from DB
        if user.stripe_subscription_id == subscription_id:
            user.stripe_subscription_id = None
            if immediately:
                user.subscription_tier = SubscriptionTier.FREE
                user.subscription_status = SubscriptionStatus.INACTIVE
            await db.commit()

        return {
            "message": message,
            "subscription_id": subscription_id,
            "new_status": canceled_sub.get("status"),
            "cancel_at_period_end": canceled_sub.get("cancel_at_period_end", False),
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/cleanup-duplicate-subscriptions")
async def cleanup_duplicate_subscriptions(
    user_id: str,
    keep_subscription_id: Optional[str] = Query(None, description="ID of subscription to keep (newest if not specified)"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Find and cancel duplicate subscriptions, keeping only one.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.stripe_customer_id:
        raise HTTPException(status_code=404, detail="User not found or no Stripe customer")

    try:
        # Get active/trialing subscriptions
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status="all",
            limit=10,
        )

        active_subs = [s for s in subscriptions.data if s.get("status") in ["active", "trialing"]]

        if len(active_subs) <= 1:
            return {"message": "No duplicates found", "active_count": len(active_subs)}

        # Determine which to keep (newest by default, or specified)
        if keep_subscription_id:
            keep_sub = next((s for s in active_subs if s.get("id") == keep_subscription_id), None)
            if not keep_sub:
                raise HTTPException(status_code=400, detail="Specified subscription not found")
        else:
            # Keep the newest one
            keep_sub = max(active_subs, key=lambda s: s.get("created", 0))

        # Cancel all others immediately
        canceled = []
        for sub in active_subs:
            if sub.get("id") != keep_sub.get("id"):
                stripe.Subscription.cancel(sub.get("id"))
                canceled.append(sub.get("id"))

        # Update user's subscription ID to the kept one
        user.stripe_subscription_id = keep_sub.get("id")

        # Get tier from kept subscription
        price_id = keep_sub["items"]["data"][0]["price"]["id"]
        tier = PRICE_TO_TIER.get(price_id, SubscriptionTier.BASIC)
        user.subscription_tier = tier

        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
        }
        user.subscription_status = status_map.get(keep_sub.get("status"), SubscriptionStatus.ACTIVE)

        if keep_sub.get("trial_end"):
            user.trial_end = datetime.fromtimestamp(keep_sub["trial_end"])
        if keep_sub.get("current_period_end"):
            user.subscription_end = datetime.fromtimestamp(keep_sub["current_period_end"])

        await db.commit()

        return {
            "message": f"Cleaned up {len(canceled)} duplicate subscription(s)",
            "kept_subscription": keep_sub.get("id"),
            "canceled_subscriptions": canceled,
            "user_tier": tier.value,
            "user_status": user.subscription_status.value,
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ X (TWITTER) BOT MANAGEMENT ============

@router.get("/x-posts")
async def list_x_posts(
    status: Optional[str] = Query(None, description="Filter by status: posted, failed, pending"),
    post_type: Optional[str] = Query(None, description="Filter by type: morning_movers, platform_comparison, etc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all X posts with pagination and filters."""
    query = select(XPost)

    if status:
        query = query.where(XPost.status == XPostStatus(status))

    if post_type:
        query = query.where(XPost.post_type == XPostType(post_type))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate (newest first)
    query = query.order_by(desc(XPost.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    return {
        "posts": [p.to_dict() for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/x-posts/stats")
async def get_x_post_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get X posting statistics."""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # Total counts
    total_posts = await db.scalar(select(func.count()).select_from(XPost))
    posted_count = await db.scalar(
        select(func.count()).select_from(XPost).where(XPost.status == XPostStatus.POSTED)
    )
    failed_count = await db.scalar(
        select(func.count()).select_from(XPost).where(XPost.status == XPostStatus.FAILED)
    )

    # Recent activity
    posts_24h = await db.scalar(
        select(func.count()).select_from(XPost).where(XPost.created_at > day_ago)
    )
    posts_7d = await db.scalar(
        select(func.count()).select_from(XPost).where(XPost.created_at > week_ago)
    )

    # By type
    type_counts = {}
    for pt in XPostType:
        count = await db.scalar(
            select(func.count()).select_from(XPost)
            .where(XPost.post_type == pt)
            .where(XPost.status == XPostStatus.POSTED)
        )
        type_counts[pt.value] = count or 0

    # Get bot settings
    settings_result = await db.execute(
        select(XBotSettings).where(XBotSettings.id == "default")
    )
    bot_settings = settings_result.scalar_one_or_none()

    return {
        "totals": {
            "total": total_posts,
            "posted": posted_count,
            "failed": failed_count,
        },
        "recent": {
            "last_24h": posts_24h,
            "last_7d": posts_7d,
        },
        "by_type": type_counts,
        "bot_enabled": bot_settings.enabled if bot_settings else True,
    }


@router.get("/x-posts/{post_id}")
async def get_x_post(
    post_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed X post info."""
    result = await db.execute(select(XPost).where(XPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {"post": post.to_dict()}


@router.get("/x-bot/settings")
async def get_x_bot_settings(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get current X bot settings."""
    result = await db.execute(
        select(XBotSettings).where(XBotSettings.id == "default")
    )
    settings_row = result.scalar_one_or_none()

    if not settings_row:
        # Create default settings
        settings_row = XBotSettings(id="default", enabled=True)
        db.add(settings_row)
        await db.commit()
        await db.refresh(settings_row)

    return {"settings": settings_row.to_dict()}


@router.post("/x-bot/toggle")
async def toggle_x_bot(
    enabled: bool = Query(..., description="Enable or disable the bot"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable the X bot (master switch)."""
    result = await db.execute(
        select(XBotSettings).where(XBotSettings.id == "default")
    )
    settings_row = result.scalar_one_or_none()

    if not settings_row:
        settings_row = XBotSettings(id="default", enabled=enabled)
        db.add(settings_row)
    else:
        settings_row.enabled = enabled
        settings_row.updated_by = admin.id

    await db.commit()
    await db.refresh(settings_row)

    return {
        "message": f"X bot {'enabled' if enabled else 'disabled'}",
        "settings": settings_row.to_dict(),
    }


@router.post("/x-bot/toggle-post-type")
async def toggle_x_post_type(
    post_type: str = Query(..., description="Post type to toggle: morning_movers, platform_comparison, market_highlight, weekly_recap"),
    enabled: bool = Query(..., description="Enable or disable this post type"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a specific post type."""
    result = await db.execute(
        select(XBotSettings).where(XBotSettings.id == "default")
    )
    settings_row = result.scalar_one_or_none()

    if not settings_row:
        settings_row = XBotSettings(id="default")
        db.add(settings_row)

    # Map post type to column
    type_map = {
        "morning_movers": "morning_movers_enabled",
        "platform_comparison": "platform_comparison_enabled",
        "market_highlight": "market_highlight_enabled",
        "weekly_recap": "weekly_recap_enabled",
    }

    column_name = type_map.get(post_type)
    if not column_name:
        raise HTTPException(status_code=400, detail=f"Invalid post type: {post_type}")

    setattr(settings_row, column_name, enabled)
    settings_row.updated_by = admin.id

    await db.commit()
    await db.refresh(settings_row)

    return {
        "message": f"{post_type} {'enabled' if enabled else 'disabled'}",
        "settings": settings_row.to_dict(),
    }


@router.post("/x-bot/post-now")
async def trigger_x_post(
    post_type: str = Query(..., description="Post type to trigger: morning, afternoon, evening, weekly, stats"),
    admin: User = Depends(require_admin),
):
    """Manually trigger an X post."""
    from app.services.x_poster import run_scheduled_posts

    try:
        result = await run_scheduled_posts(post_type)
        return {
            "message": f"Triggered {post_type} post",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/x-posts/{post_id}")
async def delete_x_post_record(
    post_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an X post record (doesn't delete the tweet from X)."""
    result = await db.execute(select(XPost).where(XPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()

    return {"message": "Post record deleted", "id": post_id}
