from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class Platform(str, Enum):
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


# Market schemas
class MarketBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class MarketCreate(MarketBase):
    id: str
    platform: Platform
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: Optional[float] = None
    close_time: Optional[datetime] = None


class MarketUpdate(BaseModel):
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: Optional[float] = None
    liquidity: Optional[float] = None
    status: Optional[str] = None


class MarketResponse(MarketBase):
    id: str
    platform: Platform
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: Optional[float] = None
    liquidity: Optional[float] = None
    status: str
    close_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarketEnrichedResponse(MarketResponse):
    """Market response with computed fields for display context."""
    # Computed fields - available for ALL markets
    implied_probability: Optional[float] = None  # yes_price as percentage (0-100)
    price_change_24h: Optional[float] = None  # Change in yes_price over 24h
    price_change_7d: Optional[float] = None  # Change in yes_price over 7d
    volume_rank: Optional[int] = None  # Percentile rank 0-100 within category
    spread: Optional[float] = None  # best_ask - best_bid if available

    # Flag if AI highlight exists for this market
    has_ai_highlight: bool = False


class MarketListResponse(BaseModel):
    markets: List[MarketEnrichedResponse]
    total: int
    page: int
    page_size: int


# Snapshot schemas
class SnapshotResponse(BaseModel):
    id: int
    market_id: str
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: Optional[float] = None
    volume_24h: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    spread: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class MarketWithHistory(MarketEnrichedResponse):
    """Single market with price history and computed fields."""
    snapshots: List[SnapshotResponse] = []


# Pattern schemas
class PatternResponse(BaseModel):
    id: int
    market_id: str
    pattern_type: str
    description: Optional[str] = None
    confidence_score: Optional[float] = None
    profit_potential: Optional[float] = None
    time_sensitivity: Optional[int] = None
    risk_level: Optional[int] = None
    status: str
    detected_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Alert schemas
class AlertResponse(BaseModel):
    id: int
    title: str
    message: Optional[str] = None
    action_suggestion: Optional[str] = None
    min_tier: str
    created_at: datetime

    class Config:
        from_attributes = True


# API response from external platforms
class KalshiMarketData(BaseModel):
    ticker: str
    title: str
    subtitle: Optional[str] = None
    yes_bid: Optional[float] = None
    yes_ask: Optional[float] = None
    no_bid: Optional[float] = None
    no_ask: Optional[float] = None
    volume: Optional[float] = None
    open_interest: Optional[float] = None
    status: str
    close_time: Optional[datetime] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class PolymarketMarketData(BaseModel):
    condition_id: str
    question: str
    description: Optional[str] = None
    outcomes: List[str]
    outcome_prices: List[float]
    volume: Optional[float] = None
    volume_24h: Optional[float] = None  # From event's volume24hr
    volume_1wk: Optional[float] = None  # volume1wk
    liquidity: Optional[float] = None
    end_date: Optional[datetime] = None
    category: Optional[str] = None
    spread: Optional[float] = None  # spread field from API
    best_ask: Optional[float] = None  # bestAsk field from API
    price_change_24h: Optional[float] = None  # oneDayPriceChange from API
    image_url: Optional[str] = None  # Event/market image from API


# ============================================================================
# Cross-Platform Spotlight Schemas
# ============================================================================

class NewsHeadline(BaseModel):
    """Recent news headline related to a market."""
    title: str
    source: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


class PricePoint(BaseModel):
    """Single price point for history chart."""
    timestamp: datetime
    price: float


class PlatformPriceHistory(BaseModel):
    """Price history for one platform."""
    platform: str
    current_price: float
    price_7d_ago: Optional[float] = None
    change_7d: Optional[float] = None  # In cents
    change_7d_pct: Optional[float] = None  # As percentage
    trend: str = "stable"  # "up", "down", "stable"
    history: List[PricePoint] = []


class KeyDate(BaseModel):
    """Important date/catalyst for a market."""
    date: str
    description: str
    is_resolution_date: bool = False


class RelatedMarket(BaseModel):
    """Related market on same topic."""
    id: str
    platform: str
    title: str
    yes_price: float
    volume: float


class CrossPlatformMatch(BaseModel):
    """A single platform's view of a cross-platform matched market."""
    market_id: str
    platform: str
    title: str
    yes_price: float
    volume: float
    liquidity: Optional[float] = None
    close_time: Optional[datetime] = None


class CrossPlatformSpotlight(BaseModel):
    """
    Rich cross-platform market spotlight with full context.

    This is the main response for the spotlight endpoint - provides
    comprehensive research context for users comparing markets across platforms.
    """
    # Core identification
    match_id: str  # Unique identifier for this cross-platform match
    topic: str  # Human-readable topic name
    category: Optional[str] = None

    # Platform comparison
    kalshi: Optional[CrossPlatformMatch] = None
    polymarket: Optional[CrossPlatformMatch] = None
    price_gap_cents: float
    gap_direction: str  # "kalshi_higher", "polymarket_higher", "equal"

    # Recent news (2-3 headlines)
    news_headlines: List[NewsHeadline] = []

    # Price history (7 days)
    kalshi_history: Optional[PlatformPriceHistory] = None
    polymarket_history: Optional[PlatformPriceHistory] = None
    price_correlation: Optional[str] = None  # "moving_together", "diverging", etc.

    # Key dates and catalysts
    key_dates: List[KeyDate] = []
    resolution_date: Optional[datetime] = None
    days_until_resolution: Optional[int] = None

    # AI Analysis (3-4 sentences)
    ai_analysis: Optional[str] = None
    gap_explanation: Optional[str] = None
    momentum_summary: Optional[str] = None
    key_risks: Optional[str] = None

    # Related markets
    related_markets: List[RelatedMarket] = []

    # Volume breakdown
    kalshi_volume: float = 0
    polymarket_volume: float = 0
    combined_volume: float = 0

    # Links
    kalshi_url: Optional[str] = None
    polymarket_url: Optional[str] = None

    # Metadata
    last_updated: datetime
    data_freshness: str = "live"  # "live", "cached", "stale"


class CrossPlatformSummary(BaseModel):
    """Brief summary for daily digest Cross-Platform Watch section."""
    match_id: str
    topic: str
    kalshi_price: float
    polymarket_price: float
    gap_cents: float
    gap_direction: str
    combined_volume: float
    summary: str  # 2-sentence AI summary
    trend: str  # "both_up", "both_down", "diverging", "stable"


class CrossPlatformWatchResponse(BaseModel):
    """Response for Cross-Platform Watch section in daily digest."""
    matches: List[CrossPlatformSummary]
    total_matches: int
    total_volume: float
    generated_at: datetime
