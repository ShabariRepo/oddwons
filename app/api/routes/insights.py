"""
AI Insights API Routes.

This is where the VALUE is delivered - AI-powered actionable insights.
Tier-gated access based on subscription level.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.ai_insight import AIInsight, ArbitrageOpportunity, DailyDigest
from app.services.auth import get_current_user, require_subscription
from app.services.patterns.engine import pattern_engine

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/ai")
async def get_ai_insights(
    category: Optional[str] = Query(None, description="Filter by pattern type"),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered insights based on subscription tier.

    - FREE: No access (upgrade prompt)
    - BASIC: Daily digest only, top 5 picks
    - PREMIUM: All insights + arbitrage, hourly refresh
    - PRO: Everything + deep analysis, real-time
    """
    tier = user.subscription_tier

    # FREE tier - no access
    if tier == SubscriptionTier.FREE or tier is None:
        return {
            "insights": [],
            "message": "Upgrade to Basic to access AI-powered insights",
            "upgrade_url": "/pricing",
            "tier": "free"
        }

    # Build query based on tier
    query = (
        select(AIInsight)
        .where(AIInsight.status == "active")
        .where(AIInsight.expires_at > datetime.utcnow())
    )

    if category:
        query = query.where(AIInsight.pattern_type == category)

    # Tier-based filtering
    if tier == SubscriptionTier.BASIC:
        # Basic: Only high-confidence insights (score > 70)
        query = query.where(AIInsight.confidence_score >= 70)
        tier_limit = min(limit, 5)
        refresh_interval = "daily"
    elif tier == SubscriptionTier.PREMIUM:
        # Premium: Medium+ confidence (score > 50)
        query = query.where(AIInsight.confidence_score >= 50)
        tier_limit = min(limit, 20)
        refresh_interval = "hourly"
    else:  # PRO
        # Pro: All insights
        tier_limit = limit
        refresh_interval = "real-time"

    query = query.order_by(
        AIInsight.confidence_score.desc(),
        AIInsight.created_at.desc()
    ).limit(tier_limit)

    result = await db.execute(query)
    insights = result.scalars().all()

    # Format response
    response_insights = []
    for i in insights:
        insight_data = {
            "id": i.id,
            "market_id": i.market_id,
            "platform": i.platform,
            "recommendation": i.recommendation,
            "confidence_score": i.confidence_score,
            "one_liner": i.one_liner,
            "time_sensitivity": i.time_sensitivity,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }

        # Premium+ get full reasoning
        if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
            insight_data["reasoning"] = i.reasoning
            insight_data["risk_factors"] = i.risk_factors
            insight_data["suggested_position"] = i.suggested_position

        # Pro gets edge explanation
        if tier == SubscriptionTier.PRO:
            insight_data["edge_explanation"] = i.edge_explanation

        response_insights.append(insight_data)

    response = {
        "insights": response_insights,
        "count": len(response_insights),
        "tier": tier.value if tier else "free",
        "refresh": refresh_interval,
    }

    # Add upgrade prompts for non-Pro users
    if tier == SubscriptionTier.BASIC:
        response["upgrade_prompt"] = "Upgrade to Premium for full reasoning and arbitrage alerts"
    elif tier == SubscriptionTier.PREMIUM:
        response["upgrade_prompt"] = "Upgrade to Pro for edge explanations and real-time alerts"

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
    Get the daily digest based on subscription tier.
    """
    tier = user.subscription_tier

    if tier == SubscriptionTier.FREE or tier is None:
        return {
            "digest": None,
            "message": "Upgrade to Basic to access daily digests",
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
            "message": "Daily digest not yet available. Check back soon.",
            "tier": tier.value
        }

    # Build response based on tier
    response_digest = {
        "market_sentiment": digest.market_sentiment,
        "generated_at": digest.created_at.isoformat() if digest.created_at else None,
    }

    # All tiers get top picks
    response_digest["top_picks"] = digest.top_picks or []

    # Premium+ get avoid list and watchlist
    if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
        response_digest["avoid_list"] = digest.avoid_list or []
        response_digest["watchlist"] = digest.watchlist or []

    # Pro gets arbitrage opportunities
    if tier == SubscriptionTier.PRO:
        response_digest["arbitrage_opportunities"] = digest.arbitrage_opportunities or []

    return {
        "digest": response_digest,
        "tier": tier.value
    }


@router.get("/stats")
async def get_insight_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about available insights."""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    # Count active insights
    total_active = await db.scalar(
        select(func.count())
        .where(AIInsight.status == "active")
        .where(AIInsight.expires_at > now)
    )

    # Count by recommendation
    strong_bets = await db.scalar(
        select(func.count())
        .where(AIInsight.status == "active")
        .where(AIInsight.recommendation == "STRONG_BET")
        .where(AIInsight.created_at > day_ago)
    )

    # Count arbitrage opportunities
    arb_count = await db.scalar(
        select(func.count())
        .where(ArbitrageOpportunity.status == "active")
        .where(ArbitrageOpportunity.expires_at > now)
    )

    # Average confidence
    avg_confidence = await db.scalar(
        select(func.avg(AIInsight.confidence_score))
        .where(AIInsight.status == "active")
        .where(AIInsight.created_at > day_ago)
    )

    return {
        "active_insights": total_active or 0,
        "strong_bets_24h": strong_bets or 0,
        "arbitrage_opportunities": arb_count or 0,
        "avg_confidence_24h": round(avg_confidence or 0, 2),
        "timestamp": now.isoformat(),
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
