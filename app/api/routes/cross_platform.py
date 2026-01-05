"""
Cross-Platform Market Comparison API.

Provides rich context for markets that exist on both Kalshi and Polymarket.
This is a RESEARCH COMPANION - we inform and contextualize, not recommend bets.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.cross_platform import CrossPlatformService
from app.schemas.market import (
    CrossPlatformSpotlight,
    CrossPlatformWatchResponse,
)
from app.services.auth import get_current_user_optional, get_current_user
from app.models.user import User

router = APIRouter(prefix="/cross-platform", tags=["cross-platform"])


@router.get("/matches", response_model=List[dict])
async def list_cross_platform_matches(
    min_volume: float = Query(1000, description="Minimum combined volume"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List all cross-platform market matches.

    Returns markets that exist on both Kalshi and Polymarket for the same event.
    Sorted by combined volume.
    """
    service = CrossPlatformService(db)
    matches = await service.find_all_matches(min_volume=min_volume)

    return [
        {
            "match_id": m.match_id,
            "topic": m.topic,
            "category": m.category,
            "kalshi_price": (m.kalshi_price or 0) * 100,
            "polymarket_price": (m.poly_price or 0) * 100,
            "gap_cents": abs((m.kalshi_price or 0) * 100 - (m.poly_price or 0) * 100),
            "combined_volume": (m.kalshi_volume or 0) + (m.poly_volume or 0),
        }
        for m in matches
    ]


@router.get("/spotlight/{match_id}", response_model=CrossPlatformSpotlight)
async def get_market_spotlight(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get rich spotlight for a cross-platform market match.

    Includes:
    - Price comparison across platforms
    - Recent news headlines (2-3)
    - 7-day price history
    - Key dates and catalysts
    - AI analysis (3-4 sentences)
    - Related markets
    - Volume breakdown

    Requires authentication.
    """
    service = CrossPlatformService(db)
    spotlight = await service.get_spotlight(match_id)

    if not spotlight:
        raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")

    return spotlight


@router.get("/spotlights", response_model=List[CrossPlatformSpotlight])
async def list_all_spotlights(
    limit: int = Query(5, le=20, description="Max number of spotlights"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get spotlights for top cross-platform matches.

    Returns full spotlight data for the top matches by volume.
    Requires authentication.
    """
    service = CrossPlatformService(db)
    return await service.get_all_spotlights(limit=limit)


@router.get("/watch", response_model=CrossPlatformWatchResponse)
async def get_cross_platform_watch(
    limit: int = Query(3, le=10, description="Number of matches to include"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get Cross-Platform Watch section for daily digest.

    Returns summary of top cross-platform matches with:
    - Price comparison
    - Gap analysis
    - 2-sentence summary each

    Free tier gets top 3, premium gets more.
    """
    service = CrossPlatformService(db)
    return await service.get_cross_platform_watch(limit=limit)


@router.get("/stats")
async def get_cross_platform_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about cross-platform market coverage.
    """
    service = CrossPlatformService(db)
    matches = await service.find_all_matches()

    total_volume = sum((m.kalshi_volume or 0) + (m.poly_volume or 0) for m in matches)
    avg_gap = (
        sum(abs((m.kalshi_price or 0) - (m.poly_price or 0)) * 100 for m in matches) / len(matches)
        if matches else 0
    )

    # Categorize gaps
    gaps_over_5 = len([m for m in matches if abs((m.kalshi_price or 0) - (m.poly_price or 0)) * 100 >= 5])
    gaps_2_to_5 = len([m for m in matches if 2 <= abs((m.kalshi_price or 0) - (m.poly_price or 0)) * 100 < 5])
    gaps_under_2 = len([m for m in matches if abs((m.kalshi_price or 0) - (m.poly_price or 0)) * 100 < 2])

    return {
        "total_matches": len(matches),
        "total_combined_volume": total_volume,
        "average_gap_cents": round(avg_gap, 2),
        "gaps_over_5_cents": gaps_over_5,
        "gaps_2_to_5_cents": gaps_2_to_5,
        "gaps_under_2_cents": gaps_under_2,
        "categories": list(set(m.category for m in matches)),
        "last_updated": datetime.utcnow().isoformat(),
    }
