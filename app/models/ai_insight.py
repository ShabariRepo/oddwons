"""
Database models for AI-powered insights and market highlights.
COMPANION APP: We inform and contextualize, NOT recommend bets.
Users pay for curated market summaries, context on price movements, and time savings.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Numeric, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class ArbitrageType(str, enum.Enum):
    CROSS_PLATFORM = "CROSS_PLATFORM"
    RELATED_MARKET = "RELATED_MARKET"
    TEMPORAL = "TEMPORAL"
    HEDGE = "HEDGE"


class AIInsight(Base):
    """
    AI-generated market highlights and context.
    COMPANION APPROACH: We inform and summarize, not recommend bets.

    Think Bloomberg Terminal for prediction markets, NOT a tipster.
    """
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String(255), nullable=False, index=True)
    market_title = Column(Text)  # Store title for display
    platform = Column(String(50), nullable=False)
    category = Column(String(50))  # politics, sports, crypto, etc.
    image_url = Column(Text)  # Market/event image URL from platform

    # Market Summary (COMPANION STYLE)
    summary = Column(Text, nullable=False)  # What this market is about
    current_odds = Column(JSON)  # {"yes": 0.62, "no": 0.38}
    implied_probability = Column(Text)  # "62% chance of X happening"

    # Activity & Movement
    volume_note = Column(String(100))  # "High volume", "Moderate", "Low liquidity"
    recent_movement = Column(String(100))  # "+5% this week", "Stable", "Down 3%"
    movement_context = Column(Text)  # Why it moved or "No significant changes"

    # Upcoming Events
    upcoming_catalyst = Column(Text)  # "Key event date" or "None scheduled"

    # Analyst Context
    analyst_note = Column(Text)  # One sentence of helpful context

    # Ranking (for display order, NOT betting confidence)
    interest_score = Column(Integer)  # 0-100, how interesting/notable this market is

    # Source Articles (THE HOMEWORK - from Gemini web search)
    source_articles = Column(JSON)  # [{"title": "", "url": "", "source": "", "date": ""}]
    news_context = Column(JSON)     # Full Gemini response for transparency

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime)
    status = Column(String(20), default="active")

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_insights_category_recent', 'category', 'created_at'),
        Index('idx_insights_platform_recent', 'platform', 'created_at'),
        Index('idx_insights_interest', 'interest_score', 'created_at'),
    )


class ArbitrageOpportunity(Base):
    """
    Cross-platform and related market arbitrage opportunities.
    Found by AI analysis comparing markets.
    """
    __tablename__ = "arbitrage_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_type = Column(String(50), nullable=False)  # CROSS_PLATFORM, RELATED_MARKET, etc.
    description = Column(Text, nullable=False)

    # Market references
    kalshi_market_id = Column(String(255))
    kalshi_market_title = Column(Text)
    polymarket_market_id = Column(String(255))
    polymarket_market_title = Column(Text)

    # Opportunity details
    edge_percentage = Column(Numeric(5, 2))  # e.g., 3.50 for 3.5%
    execution_steps = Column(JSON)  # ["step1", "step2"]
    risks = Column(JSON)  # ["risk1", "risk2"]
    confidence_score = Column(Integer)  # 0-100

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime)
    status = Column(String(50), default="active")

    __table_args__ = (
        Index('idx_arbitrage_active', 'created_at',
              postgresql_where=(status == 'active')),
        Index('idx_arbitrage_type', 'opportunity_type', 'created_at'),
    )


class DailyDigest(Base):
    """
    Pre-generated daily digest for each tier.
    COMPANION APPROACH: News briefing, not betting tips.
    """
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_date = Column(DateTime, nullable=False, index=True)
    tier = Column(String(20), nullable=False)  # basic, premium, pro

    # Digest content (COMPANION STYLE - news briefing)
    headline = Column(Text)  # One sentence summary of today's landscape
    top_movers = Column(JSON)  # Markets with notable price movements
    most_active = Column(JSON)  # High volume markets
    upcoming_catalysts = Column(JSON)  # Events that could move markets
    category_snapshots = Column(JSON)  # {"politics": "summary", "sports": "summary"}
    notable_price_gaps = Column(JSON)  # Cross-platform price differences

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_digest_date_tier', 'digest_date', 'tier', unique=True),
    )
