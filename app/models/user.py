from sqlalchemy import Column, String, Boolean, DateTime, Enum, Float
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class SubscriptionTier(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INACTIVE = "inactive"


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    # Profile
    name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), nullable=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE)

    # Stripe
    stripe_customer_id = Column(String, unique=True, index=True)
    stripe_subscription_id = Column(String, unique=True)

    # Subscription dates
    subscription_start = Column(DateTime)
    subscription_end = Column(DateTime)
    trial_end = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)

    @property
    def is_subscribed(self) -> bool:
        """Check if user has an active subscription."""
        return (
            self.subscription_tier is not None and
            self.subscription_status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
        )

    @property
    def tier_level(self) -> int:
        """Get numeric tier level for comparison."""
        if self.subscription_tier is None:
            return 0
        levels = {
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PREMIUM: 2,
            SubscriptionTier.PRO: 3,
        }
        return levels.get(self.subscription_tier, 0)
