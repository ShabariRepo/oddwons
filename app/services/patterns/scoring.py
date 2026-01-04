import logging
from typing import List, Dict, Any
from datetime import datetime

from .base import PatternResult, PatternType

logger = logging.getLogger(__name__)


class PatternScorer:
    """Scores and ranks pattern detection results."""

    # Weight configurations for different factors
    DEFAULT_WEIGHTS = {
        "confidence": 0.35,
        "profit_potential": 0.35,
        "time_sensitivity": 0.15,
        "risk_adjusted": 0.15,
    }

    # Pattern type bonuses (some patterns are more reliable)
    PATTERN_BONUSES = {
        PatternType.CROSS_PLATFORM_ARB: 15,  # Arbitrage is more reliable
        PatternType.RELATED_MARKET_ARB: 10,
        PatternType.VOLUME_SPIKE: 5,
        PatternType.RAPID_PRICE_CHANGE: 5,
        PatternType.TREND_REVERSAL: 0,
        PatternType.SUPPORT_BREAK: 0,
        PatternType.RESISTANCE_BREAK: 0,
        PatternType.VOLUME_DIVERGENCE: -5,  # Less reliable
        PatternType.UNUSUAL_FLOW: -5,
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def score(self, pattern: PatternResult) -> float:
        """Calculate overall score for a pattern."""
        # Base weighted score
        confidence_score = pattern.confidence_score * self.weights["confidence"]
        profit_score = pattern.profit_potential * self.weights["profit_potential"]

        # Time sensitivity (normalized to 0-100)
        time_score = (pattern.time_sensitivity / 5) * 100 * self.weights["time_sensitivity"]

        # Risk-adjusted score (higher confidence with lower risk = better)
        risk_penalty = (pattern.risk_level - 1) / 4  # 0 to 1
        risk_adjusted = (pattern.confidence_score * (1 - risk_penalty * 0.3)) * self.weights["risk_adjusted"]

        # Calculate base score
        base_score = confidence_score + profit_score + time_score + risk_adjusted

        # Apply pattern type bonus/penalty
        bonus = self.PATTERN_BONUSES.get(pattern.pattern_type, 0)

        # Final score capped at 100
        final_score = min(100, max(0, base_score + bonus))

        return round(final_score, 2)

    def rank(self, patterns: List[PatternResult]) -> List[PatternResult]:
        """Rank patterns by their overall score."""
        # Calculate scores and sort
        scored = [(p, self.score(p)) for p in patterns]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in scored]

    def filter_by_tier(
        self,
        patterns: List[PatternResult],
        tier: str
    ) -> List[PatternResult]:
        """Filter patterns based on subscription tier."""
        tier_thresholds = {
            "basic": 70,      # Only high-quality patterns
            "premium": 50,    # Medium and high quality
            "pro": 30,        # All significant patterns
        }

        threshold = tier_thresholds.get(tier, 50)

        return [p for p in patterns if self.score(p) >= threshold]

    def categorize(self, patterns: List[PatternResult]) -> Dict[str, List[PatternResult]]:
        """Categorize patterns by type and quality."""
        categories = {
            "high_confidence": [],
            "high_profit": [],
            "time_sensitive": [],
            "low_risk": [],
            "arbitrage": [],
        }

        for p in patterns:
            if p.confidence_score >= 75:
                categories["high_confidence"].append(p)

            if p.profit_potential >= 70:
                categories["high_profit"].append(p)

            if p.time_sensitivity >= 4:
                categories["time_sensitive"].append(p)

            if p.risk_level <= 2:
                categories["low_risk"].append(p)

            if p.pattern_type in [PatternType.CROSS_PLATFORM_ARB, PatternType.RELATED_MARKET_ARB]:
                categories["arbitrage"].append(p)

        return categories

    def get_top_opportunities(
        self,
        patterns: List[PatternResult],
        limit: int = 10,
        min_score: float = 40
    ) -> List[Dict[str, Any]]:
        """Get top opportunities with scores."""
        ranked = self.rank(patterns)

        results = []
        for p in ranked[:limit]:
            score = self.score(p)
            if score < min_score:
                continue

            results.append({
                "pattern": p.to_dict(),
                "overall_score": score,
                "tier_required": self._get_required_tier(score),
                "urgency": self._get_urgency_label(p.time_sensitivity),
                "risk_label": self._get_risk_label(p.risk_level),
            })

        return results

    def _get_required_tier(self, score: float) -> str:
        """Determine minimum tier required for a pattern."""
        if score >= 70:
            return "basic"
        elif score >= 50:
            return "premium"
        else:
            return "pro"

    def _get_urgency_label(self, time_sensitivity: int) -> str:
        """Get human-readable urgency label."""
        labels = {
            5: "Act Now",
            4: "High Priority",
            3: "Moderate",
            2: "Low Priority",
            1: "No Rush",
        }
        return labels.get(time_sensitivity, "Unknown")

    def _get_risk_label(self, risk_level: int) -> str:
        """Get human-readable risk label."""
        labels = {
            1: "Very Low",
            2: "Low",
            3: "Moderate",
            4: "High",
            5: "Very High",
        }
        return labels.get(risk_level, "Unknown")
