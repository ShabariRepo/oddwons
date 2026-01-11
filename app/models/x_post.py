"""X (Twitter) Post tracking model."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class XPostType(str, enum.Enum):
    MORNING_MOVERS = "morning_movers"
    PLATFORM_COMPARISON = "platform_comparison"
    MARKET_HIGHLIGHT = "market_highlight"
    WEEKLY_RECAP = "weekly_recap"
    DAILY_STATS = "daily_stats"
    MANUAL = "manual"


class XPostStatus(str, enum.Enum):
    POSTED = "posted"
    FAILED = "failed"
    PENDING = "pending"


class XPost(Base):
    """Track all X (Twitter) posts for admin visibility."""
    __tablename__ = "x_posts"

    id = Column(String, primary_key=True)  # UUID

    # Twitter data
    tweet_id = Column(String, unique=True, index=True)  # Twitter's tweet ID
    tweet_url = Column(String)  # Full URL to the tweet

    # Post metadata
    post_type = Column(Enum(XPostType), nullable=False)
    status = Column(Enum(XPostStatus), default=XPostStatus.PENDING)

    # Content
    content = Column(Text, nullable=False)  # The actual tweet text
    has_image = Column(Boolean, default=False)
    image_url = Column(String)  # URL of attached image (if any)

    # Context (what data was used to generate this)
    market_data = Column(JSON)  # The market data passed to Groq
    insight_ids = Column(JSON)  # List of AIInsight IDs used
    market_ids = Column(JSON)  # List of Market IDs referenced

    # Error tracking
    error_message = Column(Text)  # If failed, why
    retry_count = Column(String, default="0")

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    posted_at = Column(DateTime)  # When actually posted to X

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "tweet_id": self.tweet_id,
            "tweet_url": self.tweet_url,
            "post_type": self.post_type.value if self.post_type else None,
            "status": self.status.value if self.status else None,
            "content": self.content,
            "has_image": self.has_image,
            "image_url": self.image_url,
            "market_data": self.market_data,
            "insight_ids": self.insight_ids,
            "market_ids": self.market_ids,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
        }


class XBotSettings(Base):
    """Global settings for the X bot."""
    __tablename__ = "x_bot_settings"

    id = Column(String, primary_key=True, default="default")  # Single row

    # Bot control
    enabled = Column(Boolean, default=True)  # Master on/off switch

    # Per-post-type toggles
    morning_movers_enabled = Column(Boolean, default=True)
    platform_comparison_enabled = Column(Boolean, default=True)
    market_highlight_enabled = Column(Boolean, default=True)
    weekly_recap_enabled = Column(Boolean, default=True)

    # Rate limiting
    max_posts_per_day = Column(String, default="10")

    # Last updated
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String)  # Admin user ID who last changed settings

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "enabled": self.enabled,
            "morning_movers_enabled": self.morning_movers_enabled,
            "platform_comparison_enabled": self.platform_comparison_enabled,
            "market_highlight_enabled": self.market_highlight_enabled,
            "weekly_recap_enabled": self.weekly_recap_enabled,
            "max_posts_per_day": int(self.max_posts_per_day) if self.max_posts_per_day else 10,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by,
        }
