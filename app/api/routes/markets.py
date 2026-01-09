from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, literal
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.core.database import get_db, get_redis
from app.models.market import Market, MarketSnapshot, Platform
from app.models.ai_insight import AIInsight
from app.schemas.market import (
    MarketResponse,
    MarketEnrichedResponse,
    MarketListResponse,
    MarketWithHistory,
    SnapshotResponse,
)

router = APIRouter(prefix="/markets", tags=["markets"])


async def compute_enriched_fields(
    markets: List[Market],
    db: AsyncSession
) -> List[MarketEnrichedResponse]:
    """
    Compute derived fields for all markets:
    - implied_probability: yes_price as percentage
    - price_change_24h: current - 24h ago
    - price_change_7d: current - 7d ago
    - volume_rank: percentile within category
    - spread: best_ask - best_bid
    - has_ai_highlight: whether AI insight exists
    """
    if not markets:
        return []

    market_ids = [m.id for m in markets]
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    # Get latest snapshots for spread (best_bid, best_ask)
    latest_snapshots = {}
    snapshot_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id.in_(market_ids))
        .order_by(MarketSnapshot.market_id, MarketSnapshot.timestamp.desc())
        .distinct(MarketSnapshot.market_id)
    )
    for snap in snapshot_result.scalars().all():
        latest_snapshots[snap.market_id] = snap

    # Get 24h ago snapshots for price_change_24h
    snapshots_24h = {}
    result_24h = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id.in_(market_ids))
        .where(MarketSnapshot.timestamp <= day_ago)
        .order_by(MarketSnapshot.market_id, MarketSnapshot.timestamp.desc())
        .distinct(MarketSnapshot.market_id)
    )
    for snap in result_24h.scalars().all():
        snapshots_24h[snap.market_id] = snap

    # Get 7d ago snapshots for price_change_7d
    snapshots_7d = {}
    result_7d = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id.in_(market_ids))
        .where(MarketSnapshot.timestamp <= week_ago)
        .order_by(MarketSnapshot.market_id, MarketSnapshot.timestamp.desc())
        .distinct(MarketSnapshot.market_id)
    )
    for snap in result_7d.scalars().all():
        snapshots_7d[snap.market_id] = snap

    # Get AI insights for has_ai_highlight flag
    ai_market_ids = set()
    ai_result = await db.execute(
        select(AIInsight.market_id)
        .where(AIInsight.market_id.in_(market_ids))
        .where(AIInsight.status == "active")
    )
    for row in ai_result.all():
        ai_market_ids.add(row[0])

    # Compute volume ranks within categories
    # Group markets by category and compute percentile
    volume_ranks = {}
    categories = set(m.category for m in markets if m.category)

    for category in categories:
        if not category:
            continue
        # Get all volumes in this category for percentile calculation
        cat_volumes_result = await db.execute(
            select(Market.id, Market.volume)
            .where(Market.category == category)
            .where(Market.status == "active")
            .order_by(Market.volume.desc().nullslast())
        )
        cat_markets = cat_volumes_result.all()
        total_in_cat = len(cat_markets)

        for rank, (mid, vol) in enumerate(cat_markets):
            if mid in market_ids:
                # Percentile: 100 = highest volume, 0 = lowest
                percentile = int(100 * (1 - rank / max(total_in_cat, 1)))
                volume_ranks[mid] = percentile

    # Build enriched responses
    enriched = []
    for market in markets:
        # Base fields from model
        response = MarketEnrichedResponse.model_validate(market)

        # Computed: implied_probability
        if market.yes_price is not None:
            response.implied_probability = round(market.yes_price * 100, 1)

        # Computed: spread from latest snapshot
        if market.id in latest_snapshots:
            snap = latest_snapshots[market.id]
            if snap.best_ask is not None and snap.best_bid is not None:
                response.spread = round(snap.best_ask - snap.best_bid, 4)

        # Computed: price_change_24h
        if market.id in snapshots_24h and market.yes_price is not None:
            old_price = snapshots_24h[market.id].yes_price
            if old_price is not None:
                response.price_change_24h = round((market.yes_price - old_price) * 100, 1)

        # Computed: price_change_7d
        if market.id in snapshots_7d and market.yes_price is not None:
            old_price = snapshots_7d[market.id].yes_price
            if old_price is not None:
                response.price_change_7d = round((market.yes_price - old_price) * 100, 1)

        # Computed: volume_rank
        response.volume_rank = volume_ranks.get(market.id)

        # Flag: has_ai_highlight
        response.has_ai_highlight = market.id in ai_market_ids

        enriched.append(response)

    return enriched


@router.get("", response_model=MarketListResponse)
async def list_markets(
    platform: Optional[str] = Query(None, description="Filter by platform (kalshi, polymarket)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: str = Query("active", description="Filter by status"),
    sort_by: str = Query("volume", description="Sort by: volume, price_change_24h, implied_probability"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List all markets with computed context fields.

    Every market returns:
    - implied_probability: yes_price as percentage (0-100)
    - price_change_24h: change in probability over 24h
    - price_change_7d: change in probability over 7d
    - volume_rank: percentile rank (0-100) within category
    - spread: bid-ask spread if available
    - has_ai_highlight: whether curated AI insight exists
    """
    query = select(Market)

    if platform:
        query = query.where(Market.platform == Platform(platform))
    if category:
        query = query.where(Market.category == category)
    if status:
        query = query.where(Market.status == status)

    # Always filter out resolved markets (price at 0% or 100%)
    query = query.where(Market.yes_price > 0.02).where(Market.yes_price < 0.98)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Sort (default by volume)
    query = query.order_by(Market.volume.desc().nullslast())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    markets = list(result.scalars().all())

    # Compute enriched fields for all markets in this page
    enriched_markets = await compute_enriched_fields(markets, db)

    return MarketListResponse(
        markets=enriched_markets,
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{market_id}")
async def get_market(
    market_id: str,
    history_limit: int = Query(100, ge=1, le=1000, description="Number of historical snapshots"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full market details with price history, AI insight (if exists), and cross-platform match.

    Returns:
    - market: Full market data with computed fields
    - price_history: Historical price/volume data
    - ai_insight: AI-generated analysis if available
    - cross_platform: Cross-platform match if available
    """
    from app.models.cross_platform_match import CrossPlatformMatch

    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Fetch snapshots
    snapshot_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .limit(history_limit)
    )
    snapshots = snapshot_result.scalars().all()

    # Compute enriched fields for this single market
    enriched = await compute_enriched_fields([market], db)

    # Build price history
    price_history = [
        {
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "yes_price": s.yes_price,
            "no_price": s.no_price,
            "volume": s.volume,
            "volume_24h": s.volume_24h,
        }
        for s in reversed(snapshots)
    ]

    # Check for AI insight
    ai_insight_result = await db.execute(
        select(AIInsight)
        .where(AIInsight.market_id == market_id)
        .where(AIInsight.status == "active")
        .order_by(AIInsight.created_at.desc())
        .limit(1)
    )
    ai_insight = ai_insight_result.scalar_one_or_none()

    ai_insight_data = None
    if ai_insight:
        ai_insight_data = {
            "id": ai_insight.id,
            "summary": ai_insight.summary,
            "analyst_note": ai_insight.analyst_note,
            "upcoming_catalyst": ai_insight.upcoming_catalyst,
            "movement_context": ai_insight.movement_context,
            "source_articles": ai_insight.source_articles,
            "created_at": ai_insight.created_at.isoformat() if ai_insight.created_at else None,
        }

    # Check for cross-platform match
    cross_platform = None
    match_result = await db.execute(
        select(CrossPlatformMatch)
        .where(
            (CrossPlatformMatch.kalshi_market_id == market_id) |
            (CrossPlatformMatch.polymarket_market_id == market_id)
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
            "price_gap": abs(
                (cross_match.kalshi_yes_price or 0) - (cross_match.polymarket_yes_price or 0)
            ) if cross_match.kalshi_yes_price and cross_match.polymarket_yes_price else None,
        }

    # Use stored market URL, or construct fallback
    market_url = market.url
    if not market_url:
        platform_value = market.platform.value if hasattr(market.platform, 'value') else market.platform
        external_id = market.id
        if external_id.startswith("kalshi_"):
            external_id = external_id[7:]
        elif external_id.startswith("poly_"):
            external_id = external_id[5:]
        market_url = (
            f"https://kalshi.com/markets/{external_id}"
            if platform_value == "kalshi"
            else f"https://polymarket.com/event/{external_id}"
        )

    # Build response
    enriched_market = enriched[0]

    # Get volume_24h from latest snapshot
    volume_24h = None
    if snapshots:
        volume_24h = snapshots[0].volume_24h

    return {
        "market": {
            "id": enriched_market.id,
            "title": enriched_market.title,
            "platform": enriched_market.platform.value if hasattr(enriched_market.platform, 'value') else enriched_market.platform,
            "yes_price": enriched_market.yes_price,
            "no_price": enriched_market.no_price,
            "volume": enriched_market.volume,
            "volume_24h": volume_24h,
            "status": enriched_market.status,
            "category": enriched_market.category,
            "close_time": enriched_market.close_time.isoformat() if enriched_market.close_time else None,
            "url": market_url,
            "implied_probability": enriched_market.implied_probability,
            "price_change_24h": enriched_market.price_change_24h,
            "price_change_7d": enriched_market.price_change_7d,
            "volume_rank": enriched_market.volume_rank,
            "has_ai_highlight": enriched_market.has_ai_highlight,
            "created_at": enriched_market.created_at.isoformat() if enriched_market.created_at else None,
            "updated_at": enriched_market.updated_at.isoformat() if enriched_market.updated_at else None,
        },
        "price_history": price_history,
        "ai_insight": ai_insight_data,
        "cross_platform": cross_platform,
    }


@router.get("/{market_id}/snapshots", response_model=List[SnapshotResponse])
async def get_market_snapshots(
    market_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get historical snapshots for a market."""
    result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    snapshots = result.scalars().all()

    return [SnapshotResponse.model_validate(s) for s in snapshots]


@router.get("/cached/{market_id}")
async def get_cached_market(
    market_id: str,
    r: redis.Redis = Depends(get_redis),
):
    """Get cached market data from Redis (fast)."""
    data = await r.hgetall(f"market:{market_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Market not found in cache")

    return {
        "market_id": market_id,
        "yes_price": float(data.get("yes_price", 0)),
        "no_price": float(data.get("no_price", 0)),
        "volume": float(data.get("volume", 0)),
        "liquidity": float(data.get("liquidity", 0)) if data.get("liquidity") else None,
        "updated_at": data.get("updated_at"),
        "source": "cache",
    }


@router.get("/stats/summary")
async def get_market_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics."""
    # Count by platform
    kalshi_count = await db.scalar(
        select(func.count()).where(Market.platform == Platform.KALSHI)
    )
    poly_count = await db.scalar(
        select(func.count()).where(Market.platform == Platform.POLYMARKET)
    )

    # Total volume
    total_volume = await db.scalar(
        select(func.sum(Market.volume))
    )

    # Last collection time - try Redis but don't fail if unavailable
    last_collection = None
    try:
        from app.core.database import get_redis
        r = await get_redis()
        last_collection = await r.get("last_collection")
    except Exception:
        pass  # Redis unavailable, that's OK

    return {
        "kalshi_markets": kalshi_count or 0,
        "polymarket_markets": poly_count or 0,
        "total_markets": (kalshi_count or 0) + (poly_count or 0),
        "total_volume": total_volume or 0,
        "last_collection": last_collection,
    }
