from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any


class PatternType(str, Enum):
    # Volume patterns
    VOLUME_SPIKE = "volume_spike"
    UNUSUAL_FLOW = "unusual_flow"
    VOLUME_DIVERGENCE = "volume_divergence"

    # Price patterns
    RAPID_PRICE_CHANGE = "rapid_price_change"
    TREND_REVERSAL = "trend_reversal"
    SUPPORT_BREAK = "support_break"
    RESISTANCE_BREAK = "resistance_break"

    # Arbitrage patterns
    CROSS_PLATFORM_ARB = "cross_platform_arbitrage"
    RELATED_MARKET_ARB = "related_market_arbitrage"

    # Sentiment patterns
    LARGE_ORDER = "large_order"
    MARKET_MAKER_ACTIVITY = "market_maker_activity"


@dataclass
class PatternResult:
    """Result from a pattern detection."""
    pattern_type: PatternType
    market_id: str
    confidence_score: float  # 0-100
    profit_potential: float  # 0-100
    time_sensitivity: int  # 1-5 (5 = most urgent)
    risk_level: int  # 1-5 (5 = highest risk)

    description: str
    action_suggestion: str

    # Supporting data
    data: Dict[str, Any] = field(default_factory=dict)
    related_markets: List[str] = field(default_factory=list)

    # Timestamps
    detected_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        # Set default expiry based on time sensitivity
        if self.expires_at is None:
            hours_map = {5: 1, 4: 4, 3: 12, 2: 24, 1: 48}
            hours = hours_map.get(self.time_sensitivity, 24)
            self.expires_at = self.detected_at + timedelta(hours=hours)

    @property
    def overall_score(self) -> float:
        """Calculate overall opportunity score."""
        # Weighted average: confidence 40%, profit 40%, urgency 20%
        urgency_normalized = (self.time_sensitivity / 5) * 100
        return (
            self.confidence_score * 0.4 +
            self.profit_potential * 0.4 +
            urgency_normalized * 0.2
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "market_id": self.market_id,
            "confidence_score": self.confidence_score,
            "profit_potential": self.profit_potential,
            "time_sensitivity": self.time_sensitivity,
            "risk_level": self.risk_level,
            "overall_score": self.overall_score,
            "description": self.description,
            "action_suggestion": self.action_suggestion,
            "data": self.data,
            "related_markets": self.related_markets,
            "detected_at": self.detected_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class MarketData:
    """Market data for pattern analysis."""
    market_id: str
    platform: str
    title: str

    # Current prices
    yes_price: Optional[float] = None
    no_price: Optional[float] = None

    # Volume
    volume: Optional[float] = None
    volume_24h: Optional[float] = None

    # Orderbook
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    spread: Optional[float] = None

    # Historical data (list of snapshots)
    price_history: List[Dict[str, Any]] = field(default_factory=list)
    volume_history: List[Dict[str, Any]] = field(default_factory=list)

    # Image
    image_url: Optional[str] = None

    @property
    def mid_price(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return self.yes_price


class PatternDetector(ABC):
    """Base class for pattern detectors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def detect(self, market: MarketData) -> List[PatternResult]:
        """Detect patterns in a single market."""
        pass

    @abstractmethod
    async def detect_batch(self, markets: List[MarketData]) -> List[PatternResult]:
        """Detect patterns across multiple markets."""
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
