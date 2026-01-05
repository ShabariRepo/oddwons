"""
Cross-Platform Match model for storing dynamically discovered market matches.
"""
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CrossPlatformMatch(Base):
    """
    Stores markets that exist on both Kalshi and Polymarket.
    Discovered via fuzzy title matching, not hardcoded patterns.
    """
    __tablename__ = "cross_platform_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(255), unique=True, nullable=False, index=True)  # URL-friendly ID
    topic = Column(String(500), nullable=False)  # Human-readable topic
    category = Column(String(100), index=True)

    # Kalshi side
    kalshi_market_id = Column(String(255), ForeignKey("markets.id"), index=True)
    kalshi_title = Column(Text)
    kalshi_yes_price = Column(Float)  # 0-1 (decimal)
    kalshi_volume = Column(Float)
    kalshi_close_time = Column(DateTime)

    # Polymarket side
    polymarket_market_id = Column(String(255), ForeignKey("markets.id"), index=True)
    polymarket_title = Column(Text)
    polymarket_yes_price = Column(Float)  # 0-1 (decimal)
    polymarket_volume = Column(Float)
    polymarket_close_time = Column(DateTime)

    # Computed fields
    price_gap_cents = Column(Float)  # Gap in cents (0-100 scale)
    gap_direction = Column(String(20))  # "kalshi_higher", "polymarket_higher", "equal"
    combined_volume = Column(Float)
    similarity_score = Column(Float)  # How confident is the match (0-1)

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # AI-generated content (cached)
    ai_analysis = Column(Text)
    news_headlines = Column(JSON)
    gap_explanation = Column(Text)
    momentum_summary = Column(Text)
    key_risks = Column(Text)

    # Timestamps
    discovered_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    ai_generated_at = Column(DateTime)  # When AI content was last generated

    # Relationships
    kalshi_market = relationship("Market", foreign_keys=[kalshi_market_id])
    polymarket_market = relationship("Market", foreign_keys=[polymarket_market_id])

    def __repr__(self):
        return f"<CrossPlatformMatch {self.match_id}: K={self.kalshi_yes_price:.0%} P={self.polymarket_yes_price:.0%}>"
