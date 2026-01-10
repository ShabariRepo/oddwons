from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db, get_redis
from app.models.market import Pattern, Alert
from app.models.user import User
from app.services.patterns.engine import pattern_engine
from app.services.patterns.scoring import PatternScorer
from app.services.alerts import alert_generator
from app.services.auth import get_current_user, require_admin

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("")
async def list_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    market_id: Optional[str] = Query(None, description="Filter by market ID"),
    min_score: float = Query(0, description="Minimum overall score"),
    status: str = Query("active", description="Pattern status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List detected patterns with optional filters. Requires authentication."""
    query = select(Pattern).where(Pattern.status == status)

    if pattern_type:
        query = query.where(Pattern.pattern_type == pattern_type)
    if market_id:
        query = query.where(Pattern.market_id == market_id)

    # Order by confidence and recency
    query = query.order_by(
        Pattern.confidence_score.desc().nullslast(),
        Pattern.detected_at.desc()
    )
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    patterns = result.scalars().all()

    # Filter by score if needed
    scorer = PatternScorer()

    response_patterns = []
    for p in patterns:
        pattern_data = {
            "id": p.id,
            "market_id": p.market_id,
            "pattern_type": p.pattern_type,
            "description": p.description,
            "confidence_score": p.confidence_score,
            "profit_potential": p.profit_potential,
            "time_sensitivity": p.time_sensitivity,
            "risk_level": p.risk_level,
            "status": p.status,
            "detected_at": p.detected_at.isoformat() if p.detected_at else None,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            "data": p.data,
        }

        # Calculate overall score
        overall = (
            (p.confidence_score or 0) * 0.4 +
            (p.profit_potential or 0) * 0.4 +
            ((p.time_sensitivity or 1) / 5 * 100) * 0.2
        )
        pattern_data["overall_score"] = round(overall, 2)

        if overall >= min_score:
            response_patterns.append(pattern_data)

    return {
        "patterns": response_patterns,
        "total": len(response_patterns),
        "offset": offset,
        "limit": limit,
    }


@router.get("/opportunities")
async def get_top_opportunities(
    tier: str = Query("basic", description="Subscription tier (basic, premium, pro)"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get top opportunities for a subscription tier. Requires authentication."""
    # Get active patterns
    result = await db.execute(
        select(Pattern)
        .where(Pattern.status == "active")
        .where(Pattern.expires_at > datetime.utcnow())
        .order_by(Pattern.confidence_score.desc().nullslast())
        .limit(100)
    )
    patterns = result.scalars().all()

    # Score and filter by tier
    scorer = PatternScorer()
    tier_thresholds = {"basic": 70, "premium": 50, "pro": 30}
    threshold = tier_thresholds.get(tier, 50)

    opportunities = []
    for p in patterns:
        # Calculate overall score
        overall = (
            (p.confidence_score or 0) * 0.4 +
            (p.profit_potential or 0) * 0.4 +
            ((p.time_sensitivity or 1) / 5 * 100) * 0.2
        )

        if overall >= threshold:
            opportunities.append({
                "id": p.id,
                "market_id": p.market_id,
                "pattern_type": p.pattern_type,
                "description": p.description,
                "overall_score": round(overall, 2),
                "confidence_score": p.confidence_score,
                "profit_potential": p.profit_potential,
                "time_sensitivity": p.time_sensitivity,
                "risk_level": p.risk_level,
                "urgency": _get_urgency_label(p.time_sensitivity),
                "risk_label": _get_risk_label(p.risk_level),
                "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                "data": p.data,
            })

    # Sort by score and limit
    opportunities.sort(key=lambda x: x["overall_score"], reverse=True)

    return {
        "tier": tier,
        "opportunities": opportunities[:limit],
        "total_available": len(opportunities),
    }


@router.post("/analyze")
async def run_analysis(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger pattern analysis on current market data. ADMIN ONLY."""
    try:
        result = await pattern_engine.run_full_analysis()
        return {
            "status": "completed",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/stats")
async def get_pattern_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pattern detection statistics. Requires authentication."""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    # Count by type
    type_counts = await db.execute(
        select(Pattern.pattern_type, func.count(Pattern.id))
        .where(Pattern.detected_at >= day_ago)
        .group_by(Pattern.pattern_type)
    )

    # Count active patterns
    active_count = await db.scalar(
        select(func.count())
        .where(Pattern.status == "active")
        .where(Pattern.expires_at > now)
    )

    # Average scores
    avg_confidence = await db.scalar(
        select(func.avg(Pattern.confidence_score))
        .where(Pattern.detected_at >= day_ago)
    )

    return {
        "patterns_24h": dict(type_counts.all()),
        "active_patterns": active_count or 0,
        "avg_confidence_24h": round(avg_confidence or 0, 2),
        "timestamp": now.isoformat(),
    }


@router.get("/types")
async def list_pattern_types():
    """List all available pattern types."""
    return {
        "pattern_types": [
            {"type": "volume_spike", "category": "volume", "description": "Sudden volume increase (>3x normal)"},
            {"type": "unusual_flow", "category": "volume", "description": "Unusual directional betting activity"},
            {"type": "volume_divergence", "category": "volume", "description": "Volume up but price stable"},
            {"type": "rapid_price_change", "category": "price", "description": "Fast price movement (>10%)"},
            {"type": "trend_reversal", "category": "price", "description": "Momentum shift detected"},
            {"type": "support_break", "category": "price", "description": "Price breaks below support level"},
            {"type": "resistance_break", "category": "price", "description": "Price breaks above resistance"},
            {"type": "cross_platform_arbitrage", "category": "arbitrage", "description": "Price difference between platforms"},
            {"type": "related_market_arbitrage", "category": "arbitrage", "description": "Mispricing in related markets"},
        ]
    }


# Alerts endpoints
@router.get("/alerts")
async def get_alerts(
    tier: str = Query("basic", description="Subscription tier"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """Get recent alerts for a subscription tier. Requires authentication."""
    alerts = await alert_generator.get_alerts_for_tier(tier, limit)
    return {
        "tier": tier,
        "alerts": alerts,
        "count": len(alerts),
    }


@router.get("/alerts/stats")
async def get_alert_stats(
    current_user: User = Depends(get_current_user),
):
    """Get alert generation statistics. Requires authentication."""
    stats = await alert_generator.get_alert_stats()
    return stats


def _get_urgency_label(time_sensitivity: int) -> str:
    labels = {5: "Act Now", 4: "High Priority", 3: "Moderate", 2: "Low Priority", 1: "No Rush"}
    return labels.get(time_sensitivity, "Unknown")


def _get_risk_label(risk_level: int) -> str:
    labels = {1: "Very Low", 2: "Low", 3: "Moderate", 4: "High", 5: "Very High"}
    return labels.get(risk_level, "Unknown")
