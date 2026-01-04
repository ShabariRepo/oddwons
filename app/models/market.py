from sqlalchemy import Column, String, Float, DateTime, Integer, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class Platform(str, enum.Enum):
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


class Market(Base):
    """Core market information from prediction platforms."""
    __tablename__ = "markets"

    id = Column(String, primary_key=True)  # Platform's market ID
    platform = Column(Enum(Platform), nullable=False, index=True)

    # Market details
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, index=True)

    # Current state
    yes_price = Column(Float)  # Current YES price (0-1)
    no_price = Column(Float)   # Current NO price (0-1)
    volume = Column(Float)     # Total volume traded
    liquidity = Column(Float)  # Current liquidity

    # Status
    status = Column(String, default="active")  # active, closed, resolved
    resolution = Column(String)  # yes, no, null (for resolved markets)

    # Timestamps
    close_time = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    snapshots = relationship("MarketSnapshot", back_populates="market", lazy="dynamic")


class MarketSnapshot(Base):
    """Time-series snapshots for historical analysis."""
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, ForeignKey("markets.id"), nullable=False, index=True)

    # Price data
    yes_price = Column(Float)
    no_price = Column(Float)

    # Volume data
    volume = Column(Float)
    volume_24h = Column(Float)  # 24-hour volume

    # Orderbook data (optional)
    best_bid = Column(Float)
    best_ask = Column(Float)
    spread = Column(Float)

    # Raw orderbook (for detailed analysis)
    orderbook = Column(JSON)

    # Timestamp
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    market = relationship("Market", back_populates="snapshots")


class Pattern(Base):
    """Detected patterns and opportunities."""
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String, ForeignKey("markets.id"), nullable=False, index=True)

    # Pattern details
    pattern_type = Column(String, nullable=False)  # volume_spike, arbitrage, price_movement, etc.
    description = Column(Text)

    # Scoring
    confidence_score = Column(Float)  # 0-100
    profit_potential = Column(Float)  # 0-100
    time_sensitivity = Column(Integer)  # 1-5
    risk_level = Column(Integer)  # 1-5

    # Pattern data
    data = Column(JSON)  # Additional pattern-specific data

    # Status
    status = Column(String, default="active")  # active, expired, acted_upon

    # Timestamps
    detected_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)


class Alert(Base):
    """Generated alerts for users."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=False)

    # Alert content
    title = Column(String, nullable=False)
    message = Column(Text)
    action_suggestion = Column(Text)

    # Tier requirement
    min_tier = Column(String, default="basic")  # basic, premium, pro

    # Delivery status
    delivered = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
