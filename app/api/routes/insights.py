"""
AI Insights API Routes.

COMPANION APP: We inform and contextualize, NOT recommend bets.
This is where value is delivered - curated market summaries, context on price movements,
and time savings. Think Bloomberg Terminal for prediction markets, NOT a tipster.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.ai_insight import AIInsight, ArbitrageOpportunity, DailyDigest
from app.models.market import Market
from app.services.auth import get_current_user, require_subscription
from app.services.patterns.engine import pattern_engine
from app.services.cross_platform import CrossPlatformService

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/ai")
async def get_ai_insights(
    category: Optional[str] = Query(None, description="Filter by category (politics, sports, crypto, etc.)"),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered market highlights based on subscription tier.

    COMPANION APPROACH: We inform and contextualize, NOT recommend bets.

    - FREE: Preview (top 3 highlights, summaries only)
    - BASIC: Top highlights with context
    - PREMIUM: All highlights + movement analysis + catalysts
    - PRO: Everything + full analyst notes + price gaps
    """
    tier = user.subscription_tier

    # FREE tier - limited preview
    if tier == SubscriptionTier.FREE or tier is None:
        tier_limit = 3
        refresh_interval = "daily"
    elif tier == SubscriptionTier.BASIC:
        tier_limit = min(limit, 10)
        refresh_interval = "daily"
    elif tier == SubscriptionTier.PREMIUM:
        tier_limit = min(limit, 30)
        refresh_interval = "hourly"
    else:  # PRO
        tier_limit = limit
        refresh_interval = "real-time"

    # Build query - join with markets to filter out resolved/closed
    query = (
        select(AIInsight)
        .join(Market, AIInsight.market_id == Market.id, isouter=True)
        .where(AIInsight.status == "active")
        .where(AIInsight.expires_at > datetime.utcnow())
        # Filter out resolved markets (price at 0% or 100%)
        .where(
            (Market.id == None) |  # Allow if market not found (edge case)
            (
                (Market.status == 'active') &
                (Market.yes_price > 0.02) &
                (Market.yes_price < 0.98)
            )
        )
    )

    if category:
        query = query.where(AIInsight.category == category)

    query = query.order_by(
        AIInsight.interest_score.desc().nullslast(),
        AIInsight.created_at.desc()
    ).limit(tier_limit)

    result = await db.execute(query)
    insights = result.scalars().all()

    # Format response (COMPANION STYLE - informative, not betting advice)
    response_insights = []
    for i in insights:
        # Base data - all tiers see this
        insight_data = {
            "id": i.id,
            "market_id": i.market_id,
            "market_title": i.market_title,
            "platform": i.platform,
            "category": i.category,
            "summary": i.summary,
            "current_odds": i.current_odds,
            "implied_probability": i.implied_probability,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }

        # Basic+ get volume and movement info
        if tier and tier != SubscriptionTier.FREE:
            insight_data["volume_note"] = i.volume_note
            insight_data["recent_movement"] = i.recent_movement

        # Premium+ get full context
        if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
            insight_data["movement_context"] = i.movement_context
            insight_data["upcoming_catalyst"] = i.upcoming_catalyst

        # Pro gets analyst notes
        if tier == SubscriptionTier.PRO:
            insight_data["analyst_note"] = i.analyst_note

        response_insights.append(insight_data)

    response = {
        "insights": response_insights,
        "count": len(response_insights),
        "tier": tier.value if tier else "free",
        "refresh": refresh_interval,
    }

    # Add helpful upgrade prompts
    if tier == SubscriptionTier.FREE or tier is None:
        response["upgrade_prompt"] = "Upgrade to Basic for full market context and more highlights"
    elif tier == SubscriptionTier.BASIC:
        response["upgrade_prompt"] = "Upgrade to Premium for movement analysis and upcoming catalysts"
    elif tier == SubscriptionTier.PREMIUM:
        response["upgrade_prompt"] = "Upgrade to Pro for full analyst notes and real-time updates"

    return response


@router.get("/arbitrage")
async def get_arbitrage_opportunities(
    limit: int = Query(10, ge=1, le=20),
    user: User = Depends(require_subscription(SubscriptionTier.PREMIUM)),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cross-platform arbitrage opportunities.
    Premium+ only.
    """
    query = (
        select(ArbitrageOpportunity)
        .where(ArbitrageOpportunity.status == "active")
        .where(ArbitrageOpportunity.expires_at > datetime.utcnow())
        .order_by(
            ArbitrageOpportunity.edge_percentage.desc().nullslast(),
            ArbitrageOpportunity.created_at.desc()
        )
        .limit(limit)
    )

    result = await db.execute(query)
    opportunities = result.scalars().all()

    response_opps = []
    for opp in opportunities:
        opp_data = {
            "id": opp.id,
            "type": opp.opportunity_type,
            "description": opp.description,
            "edge_percentage": float(opp.edge_percentage) if opp.edge_percentage else None,
            "confidence_score": opp.confidence_score,
            "created_at": opp.created_at.isoformat() if opp.created_at else None,
        }

        # Pro gets execution steps
        if user.subscription_tier == SubscriptionTier.PRO:
            opp_data["execution_steps"] = opp.execution_steps
            opp_data["risks"] = opp.risks
            opp_data["kalshi_market_id"] = opp.kalshi_market_id
            opp_data["polymarket_market_id"] = opp.polymarket_market_id

        response_opps.append(opp_data)

    return {
        "arbitrage_opportunities": response_opps,
        "count": len(response_opps),
        "tier": user.subscription_tier.value,
    }


@router.get("/digest")
async def get_daily_digest(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the daily market briefing based on subscription tier.
    COMPANION APPROACH: News briefing, not betting tips.
    """
    tier = user.subscription_tier

    if tier == SubscriptionTier.FREE or tier is None:
        return {
            "digest": None,
            "message": "Upgrade to Basic to access daily market briefings",
            "upgrade_url": "/pricing"
        }

    # Get today's digest for this tier
    today = datetime.utcnow().date()
    result = await db.execute(
        select(DailyDigest)
        .where(DailyDigest.tier == tier.value.lower())
        .where(func.date(DailyDigest.digest_date) == today)
        .order_by(DailyDigest.created_at.desc())
        .limit(1)
    )
    digest = result.scalar_one_or_none()

    if not digest:
        # Try to generate one
        try:
            generated = await pattern_engine.generate_daily_digest(tier.value.lower())
            if generated:
                return {
                    "digest": generated,
                    "tier": tier.value,
                    "generated_at": datetime.utcnow().isoformat()
                }
        except Exception as e:
            pass

        return {
            "digest": None,
            "message": "Daily briefing not yet available. Check back soon.",
            "tier": tier.value
        }

    # Build response based on tier (COMPANION STYLE - news briefing)
    response_digest = {
        "headline": digest.headline,
        "generated_at": digest.created_at.isoformat() if digest.created_at else None,
    }

    # All paid tiers get top movers and category snapshots
    response_digest["top_movers"] = digest.top_movers or []
    response_digest["category_snapshots"] = digest.category_snapshots or {}

    # Premium+ get most active markets and upcoming catalysts
    if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
        response_digest["most_active"] = digest.most_active or []
        response_digest["upcoming_catalysts"] = digest.upcoming_catalysts or []

    # Premium+ get cross-platform watch (live data)
    if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
        try:
            cross_platform_service = CrossPlatformService(db)
            watch_limit = 5 if tier == SubscriptionTier.PRO else 3
            cross_platform_watch = await cross_platform_service.get_cross_platform_watch(limit=watch_limit)
            response_digest["cross_platform_watch"] = {
                "matches": [
                    {
                        "topic": m.topic,
                        "kalshi_price": m.kalshi_price,
                        "polymarket_price": m.polymarket_price,
                        "gap_cents": m.gap_cents,
                        "combined_volume": m.combined_volume,
                        "summary": m.summary,
                    }
                    for m in cross_platform_watch.matches
                ],
                "total_matches": cross_platform_watch.total_matches,
                "total_volume": cross_platform_watch.total_volume,
            }
        except Exception as e:
            response_digest["cross_platform_watch"] = {"error": str(e)}

    # Pro gets price gap analysis (legacy)
    if tier == SubscriptionTier.PRO:
        response_digest["notable_price_gaps"] = digest.notable_price_gaps or []

    return {
        "digest": response_digest,
        "tier": tier.value
    }


@router.get("/stats")
async def get_insight_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about available market highlights.
    COMPANION APPROACH: Informational stats, not betting metrics.
    """
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    # Count active highlights
    total_active = await db.scalar(
        select(func.count())
        .select_from(AIInsight)
        .where(AIInsight.status == "active")
        .where(AIInsight.expires_at > now)
    )

    # Count by category
    categories_covered = await db.scalar(
        select(func.count(func.distinct(AIInsight.category)))
        .where(AIInsight.status == "active")
        .where(AIInsight.created_at > day_ago)
    )

    # Count price gap findings
    price_gap_count = await db.scalar(
        select(func.count())
        .select_from(ArbitrageOpportunity)
        .where(ArbitrageOpportunity.status == "active")
        .where(ArbitrageOpportunity.expires_at > now)
    )

    # Count highlights by category (last 24h)
    from sqlalchemy import case
    politics_count = await db.scalar(
        select(func.count())
        .select_from(AIInsight)
        .where(AIInsight.category == "politics")
        .where(AIInsight.created_at > day_ago)
    )
    sports_count = await db.scalar(
        select(func.count())
        .select_from(AIInsight)
        .where(AIInsight.category == "sports")
        .where(AIInsight.created_at > day_ago)
    )
    crypto_count = await db.scalar(
        select(func.count())
        .select_from(AIInsight)
        .where(AIInsight.category == "crypto")
        .where(AIInsight.created_at > day_ago)
    )

    return {
        "active_highlights": total_active or 0,
        "categories_covered": categories_covered or 0,
        "price_gap_findings": price_gap_count or 0,
        "highlights_by_category": {
            "politics": politics_count or 0,
            "sports": sports_count or 0,
            "crypto": crypto_count or 0,
        },
        "last_updated": now.isoformat(),
    }


@router.post("/refresh")
async def trigger_analysis(
    user: User = Depends(require_subscription(SubscriptionTier.PRO)),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger AI analysis.
    Pro tier only - prevents abuse.
    """
    try:
        results = await pattern_engine.run_full_analysis(with_ai=True)
        return {
            "status": "completed",
            "markets_analyzed": results.get("total_markets_analyzed", 0),
            "patterns_detected": results.get("total_patterns_detected", 0),
            "ai_insights_generated": results.get("ai_insights_saved", 0),
            "timestamp": results.get("timestamp"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
