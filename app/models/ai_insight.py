"""
Database models for AI-powered insights and arbitrage opportunities.
This is where the actual value lives - actionable AI analysis.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Numeric, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class RecommendationType(str, enum.Enum):
    STRONG_BET = "STRONG_BET"
    GOOD_BET = "GOOD_BET"
    CAUTION = "CAUTION"
    AVOID = "AVOID"


class TimeSensitivity(str, enum.Enum):
    ACT_NOW = "ACT_NOW"
    HOURS = "HOURS"
    DAYS = "DAYS"
    WEEKS = "WEEKS"


class ArbitrageType(str, enum.Enum):
    CROSS_PLATFORM = "CROSS_PLATFORM"
    RELATED_MARKET = "RELATED_MARKET"
    TEMPORAL = "TEMPORAL"
    HEDGE = "HEDGE"


class AIInsight(Base):
    """
    AI-generated market insights.
    This is what users pay for - not "volume spike detected".
    """
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    pattern_type = Column(String(100))

    # AI Analysis Results
    recommendation = Column(String(50), nullable=False)  # STRONG_BET, GOOD_BET, CAUTION, AVOID
    confidence_score = Column(Integer, nullable=False)  # 0-100
    one_liner = Column(Text, nullable=False)  # Single actionable sentence
    reasoning = Column(Text)  # 2-3 sentences explaining WHY
    risk_factors = Column(JSON)  # ["risk1", "risk2"]
    suggested_position = Column(String(20))  # YES, NO, WAIT
    edge_explanation = Column(Text)  # What edge does the bettor have
    time_sensitivity = Column(String(20))  # ACT_NOW, HOURS, DAYS, WEEKS

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime)
    status = Column(String(20), default="active")

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_insights_actionable', 'confidence_score', 'created_at',
              postgresql_where=(confidence_score > 60)),
        Index('idx_insights_platform_recent', 'platform', 'created_at'),
        Index('idx_insights_recommendation', 'recommendation', 'created_at'),
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
    Cached to avoid repeated AI calls.
    """
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_date = Column(DateTime, nullable=False, index=True)
    tier = Column(String(20), nullable=False)  # basic, premium, pro

    # Digest content (JSON blob from AI)
    top_picks = Column(JSON)
    avoid_list = Column(JSON)
    market_sentiment = Column(Text)
    arbitrage_opportunities = Column(JSON)
    watchlist = Column(JSON)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_digest_date_tier', 'digest_date', 'tier', unique=True),
    )
