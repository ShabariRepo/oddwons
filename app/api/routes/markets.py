from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import redis.asyncio as redis

from app.core.database import get_db, get_redis
from app.models.market import Market, MarketSnapshot, Platform
from app.schemas.market import (
    MarketResponse,
    MarketListResponse,
    MarketWithHistory,
    SnapshotResponse,
)

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("", response_model=MarketListResponse)
async def list_markets(
    platform: Optional[str] = Query(None, description="Filter by platform (kalshi, polymarket)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: str = Query("active", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all markets with optional filters."""
    query = select(Market)

    if platform:
        query = query.where(Market.platform == Platform(platform))
    if category:
        query = query.where(Market.category == category)
    if status:
        query = query.where(Market.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.order_by(Market.volume.desc().nullslast())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    markets = result.scalars().all()

    return MarketListResponse(
        markets=[MarketResponse.model_validate(m) for m in markets],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{market_id}", response_model=MarketWithHistory)
async def get_market(
    market_id: str,
    history_limit: int = Query(100, ge=1, le=1000, description="Number of historical snapshots"),
    db: AsyncSession = Depends(get_db),
):
    """Get market details with price history."""
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

    response = MarketWithHistory.model_validate(market)
    response.snapshots = [SnapshotResponse.model_validate(s) for s in snapshots]

    return response


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
    r: redis.Redis = Depends(get_redis),
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

    # Last collection time
    last_collection = await r.get("last_collection")

    return {
        "kalshi_markets": kalshi_count or 0,
        "polymarket_markets": poly_count or 0,
        "total_markets": (kalshi_count or 0) + (poly_count or 0),
        "total_volume": total_volume or 0,
        "last_collection": last_collection,
    }
