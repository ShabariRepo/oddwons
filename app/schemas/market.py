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


class MarketListResponse(BaseModel):
    markets: List[MarketResponse]
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


class MarketWithHistory(MarketResponse):
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
    liquidity: Optional[float] = None
    end_date: Optional[datetime] = None
    category: Optional[str] = None
