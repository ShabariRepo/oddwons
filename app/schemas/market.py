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
