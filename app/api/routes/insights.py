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
from app.services.auth import get_current_user, require_subscription, require_admin, get_effective_tier
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
    tier = get_effective_tier(user)

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

    # Build query based on tier and category filter
    if category:
        # Category filter - just query that category
        query = (
            select(AIInsight)
            .where(AIInsight.status == "active")
            .where(AIInsight.expires_at > datetime.utcnow())
            .where(AIInsight.category == category)
            .order_by(
                AIInsight.interest_score.desc().nullslast(),
                AIInsight.created_at.desc()
            )
            .limit(tier_limit)
        )
        result = await db.execute(query)
        insights = result.scalars().all()
    elif tier == SubscriptionTier.FREE or tier is None:
        # FREE tier: Get variety - 1 from each top category
        insights = []
        priority_categories = ["politics", "finance", "crypto", "sports", "tech", "entertainment"]

        for cat in priority_categories:
            if len(insights) >= tier_limit:
                break

            result = await db.execute(
                select(AIInsight)
                .where(AIInsight.status == "active")
                .where(AIInsight.expires_at > datetime.utcnow())
                .where(AIInsight.category == cat)
                .order_by(
                    AIInsight.interest_score.desc().nullslast(),
                    AIInsight.created_at.desc()
                )
                .limit(1)
            )
            cat_insight = result.scalar_one_or_none()
            if cat_insight:
                insights.append(cat_insight)

        # If we still don't have enough, fill with any category
        if len(insights) < tier_limit:
            existing_ids = [i.id for i in insights]
            fill_query = (
                select(AIInsight)
                .where(AIInsight.status == "active")
                .where(AIInsight.expires_at > datetime.utcnow())
            )
            if existing_ids:
                fill_query = fill_query.where(AIInsight.id.not_in(existing_ids))
            fill_query = fill_query.order_by(
                AIInsight.interest_score.desc().nullslast(),
                AIInsight.created_at.desc()
            ).limit(tier_limit - len(insights))

            result = await db.execute(fill_query)
            insights.extend(result.scalars().all())
    else:
        # Paid tiers: Get variety via round-robin across categories
        from collections import defaultdict

        # First, get more than we need
        query = (
            select(AIInsight)
            .where(AIInsight.status == "active")
            .where(AIInsight.expires_at > datetime.utcnow())
            .order_by(
                AIInsight.interest_score.desc().nullslast(),
                AIInsight.created_at.desc()
            )
            .limit(tier_limit * 3)
        )
        result = await db.execute(query)
        all_insights = result.scalars().all()

        # Group by category
        by_category = defaultdict(list)
        for i in all_insights:
            by_category[i.category].append(i)

        # Round-robin across categories
        insights = []
        max_per_category = max(3, tier_limit // max(len(by_category), 1))
        idx = 0

        while len(insights) < tier_limit:
            added_this_round = False
            for cat in by_category:
                if len(insights) >= tier_limit:
                    break
                if idx < len(by_category[cat]) and idx < max_per_category:
                    insights.append(by_category[cat][idx])
                    added_this_round = True
            if not added_this_round:
                break
            idx += 1

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
            "image_url": i.image_url,
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


@router.get("/ai/{insight_id}")
async def get_insight_detail(
    insight_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full detail for a single AI insight.

    Includes:
    - Full market info
    - AI analysis with bro vibes
    - Source articles (THE HOMEWORK - from Gemini web search)
    - Price history
    - Cross-platform comparison if available
    """
    from app.models.market import Market, MarketSnapshot
    from app.models.cross_platform_match import CrossPlatformMatch

    tier = get_effective_tier(user)

    # Get the insight
    result = await db.execute(
        select(AIInsight).where(AIInsight.id == insight_id)
    )
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Get market details
    market_result = await db.execute(
        select(Market).where(Market.id == insight.market_id)
    )
    market = market_result.scalar_one_or_none()

    # Get price history
    history_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == insight.market_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .limit(50)
    )
    snapshots = history_result.scalars().all()

    # Check for cross-platform match
    cross_platform = None
    if market:
        match_result = await db.execute(
            select(CrossPlatformMatch)
            .where(
                (CrossPlatformMatch.kalshi_market_id == market.id) |
                (CrossPlatformMatch.polymarket_market_id == market.id)
            )
            .limit(1)
        )
        cross_match = match_result.scalar_one_or_none()
        if cross_match:
            cross_platform = {
                "match_id": cross_match.match_id,
                "topic": cross_match.topic,
                "kalshi_market_id": cross_match.kalshi_market_id,
                "polymarket_market_id": cross_match.polymarket_market_id,
                "kalshi_price": cross_match.kalshi_yes_price,
                "polymarket_price": cross_match.polymarket_yes_price,
                "gap_cents": cross_match.price_gap_cents,
                "combined_volume": cross_match.combined_volume,
            }

    # Build insight response (tier-gated content)
    insight_data = {
        "id": insight.id,
        "market_id": insight.market_id,
        "market_title": insight.market_title,
        "platform": insight.platform,
        "category": insight.category,
        "summary": insight.summary,
        "current_odds": insight.current_odds,
        "implied_probability": insight.implied_probability,
        "image_url": insight.image_url,
        "created_at": insight.created_at.isoformat() if insight.created_at else None,
    }

    # Basic+ get volume and movement
    if tier and tier != SubscriptionTier.FREE:
        insight_data["volume_note"] = insight.volume_note
        insight_data["recent_movement"] = insight.recent_movement

    # Premium+ get full context
    if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
        insight_data["movement_context"] = insight.movement_context
        insight_data["upcoming_catalyst"] = insight.upcoming_catalyst

    # Pro gets analyst notes
    if tier == SubscriptionTier.PRO:
        insight_data["analyst_note"] = insight.analyst_note

    # Build market response
    market_data = None
    if market:
        platform_value = market.platform.value if hasattr(market.platform, 'value') else market.platform
        market_data = {
            "id": market.id,
            "title": market.title,
            "platform": platform_value,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "volume": market.volume,
            "status": market.status,
            "close_time": market.close_time.isoformat() if market.close_time else None,
            "url": _get_market_url(market),
        }

    # Price history (all tiers get this)
    price_history = [
        {
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "yes_price": s.yes_price,
            "no_price": s.no_price,
            "volume": s.volume,
        }
        for s in reversed(snapshots)
    ]

    # Source articles (THE HOMEWORK) - Premium+ only
    source_articles = []
    if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
        source_articles = insight.source_articles or []

    return {
        "insight": insight_data,
        "source_articles": source_articles,
        "market": market_data,
        "price_history": price_history,
        "cross_platform": cross_platform,
        "tier": tier.value if tier else "free",
    }


def _get_market_url(market) -> str:
    """Get direct link to market on platform."""
    # Use stored URL if available
    if market.url:
        return market.url

    # Fallback: construct URL from ID
    platform_value = market.platform.value if hasattr(market.platform, 'value') else market.platform
    external_id = market.id
    if external_id.startswith("kalshi_"):
        external_id = external_id[7:]
    elif external_id.startswith("poly_"):
        external_id = external_id[5:]

    if platform_value == "kalshi":
        return f"https://kalshi.com/markets/{external_id}"
    else:
        return f"https://polymarket.com/event/{external_id}"


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
        if get_effective_tier(user) == SubscriptionTier.PRO:
            opp_data["execution_steps"] = opp.execution_steps
            opp_data["risks"] = opp.risks
            opp_data["kalshi_market_id"] = opp.kalshi_market_id
            opp_data["polymarket_market_id"] = opp.polymarket_market_id

        response_opps.append(opp_data)

    return {
        "arbitrage_opportunities": response_opps,
        "count": len(response_opps),
        "tier": get_effective_tier(user).value,
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
    tier = get_effective_tier(user)

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
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger AI analysis.
    ADMIN ONLY - prevents abuse of expensive AI operations.
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
