import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
import redis.asyncio as redis

from app.core.database import AsyncSessionLocal, get_redis
from app.models.market import Pattern, Alert
from app.services.patterns.base import PatternResult
from app.services.patterns.scoring import PatternScorer

logger = logging.getLogger(__name__)


class AlertChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class AlertGenerator:
    """Generates and manages alerts from detected patterns."""

    # Tier configurations
    TIER_CONFIG = {
        "basic": {
            "min_score": 70,
            "max_alerts_per_day": 5,
            "channels": [AlertChannel.EMAIL],
            "delay_minutes": 60,  # Delay before sending
        },
        "premium": {
            "min_score": 50,
            "max_alerts_per_day": 20,
            "channels": [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PUSH],
            "delay_minutes": 15,
        },
        "pro": {
            "min_score": 30,
            "max_alerts_per_day": 100,
            "channels": [AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.PUSH, AlertChannel.WEBHOOK],
            "delay_minutes": 0,  # Instant
        },
    }

    def __init__(self):
        self.scorer = PatternScorer()
        self._redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def generate_alerts(
        self,
        patterns: List[PatternResult],
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Generate alerts from patterns for all tiers."""
        alerts = []

        for pattern in patterns:
            score = self.scorer.score(pattern)

            # Determine which tiers get this alert
            tiers = self._get_eligible_tiers(score)

            for tier in tiers:
                alert = await self._create_alert(pattern, tier, score, session)
                if alert:
                    alerts.append(alert)

        logger.info(f"Generated {len(alerts)} alerts from {len(patterns)} patterns")
        return alerts

    def _get_eligible_tiers(self, score: float) -> List[str]:
        """Determine which subscription tiers are eligible for this score."""
        eligible = []
        for tier, config in self.TIER_CONFIG.items():
            if score >= config["min_score"]:
                eligible.append(tier)
        return eligible

    async def _create_alert(
        self,
        pattern: PatternResult,
        tier: str,
        score: float,
        session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Create an alert for a specific tier."""
        # Check rate limit
        if not await self._check_rate_limit(tier):
            return None

        # Format alert content
        title = self._format_title(pattern)
        message = self._format_message(pattern, score)
        action = pattern.action_suggestion

        # Determine minimum tier for this alert
        min_tier = "pro" if score < 50 else ("premium" if score < 70 else "basic")

        try:
            # Save to database
            stmt = insert(Alert).values(
                pattern_id=None,  # Will be linked when pattern is saved
                title=title,
                message=message,
                action_suggestion=action,
                min_tier=min_tier,
            )
            result = await session.execute(stmt)
            await session.commit()

            alert_data = {
                "id": result.inserted_primary_key[0] if result.inserted_primary_key else None,
                "title": title,
                "message": message,
                "action_suggestion": action,
                "min_tier": min_tier,
                "score": score,
                "pattern_type": pattern.pattern_type.value,
                "market_id": pattern.market_id,
                "time_sensitivity": pattern.time_sensitivity,
                "channels": [c.value for c in self.TIER_CONFIG[tier]["channels"]],
                "created_at": datetime.utcnow().isoformat(),
            }

            # Cache alert for quick access
            await self._cache_alert(alert_data)

            return alert_data

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    async def _check_rate_limit(self, tier: str) -> bool:
        """Check if tier has remaining alerts for today."""
        r = await self.get_redis()
        key = f"alert_count:{tier}:{datetime.utcnow().strftime('%Y-%m-%d')}"

        count = await r.get(key)
        max_alerts = self.TIER_CONFIG[tier]["max_alerts_per_day"]

        if count and int(count) >= max_alerts:
            return False

        # Increment counter
        await r.incr(key)
        await r.expire(key, 86400)  # 24 hour expiry

        return True

    async def _cache_alert(self, alert: Dict[str, Any]) -> None:
        """Cache alert in Redis for quick retrieval."""
        r = await self.get_redis()

        # Add to recent alerts list
        await r.lpush("recent_alerts", str(alert))
        await r.ltrim("recent_alerts", 0, 99)  # Keep last 100

        # Add to tier-specific list
        tier = alert["min_tier"]
        await r.lpush(f"alerts:{tier}", str(alert))
        await r.ltrim(f"alerts:{tier}", 0, 49)

    def _format_title(self, pattern: PatternResult) -> str:
        """Format alert title."""
        type_labels = {
            "volume_spike": "Volume Spike Alert",
            "unusual_flow": "Unusual Activity",
            "volume_divergence": "Volume Divergence",
            "rapid_price_change": "Price Movement Alert",
            "trend_reversal": "Trend Reversal",
            "support_break": "Support Break",
            "resistance_break": "Resistance Break",
            "cross_platform_arbitrage": "Arbitrage Opportunity",
            "related_market_arbitrage": "Market Mispricing",
        }

        base_title = type_labels.get(pattern.pattern_type.value, "Market Alert")

        # Add urgency indicator
        if pattern.time_sensitivity >= 4:
            return f"🔥 {base_title}"
        elif pattern.time_sensitivity >= 3:
            return f"⚡ {base_title}"
        else:
            return base_title

    def _format_message(self, pattern: PatternResult, score: float) -> str:
        """Format alert message."""
        lines = [
            pattern.description,
            "",
            f"Confidence: {pattern.confidence_score:.0f}%",
            f"Profit Potential: {pattern.profit_potential:.0f}%",
            f"Risk Level: {'🟢' * (5 - pattern.risk_level)}{'🔴' * pattern.risk_level}",
            f"Overall Score: {score:.0f}/100",
        ]

        if pattern.expires_at:
            time_left = pattern.expires_at - datetime.utcnow()
            hours_left = time_left.total_seconds() / 3600
            if hours_left > 0:
                lines.append(f"Expires in: {hours_left:.1f} hours")

        return "\n".join(lines)

    async def get_alerts_for_tier(
        self,
        tier: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent alerts for a subscription tier."""
        r = await self.get_redis()

        # Get alerts for this tier and all higher tiers
        all_alerts = []

        # Tier hierarchy: pro > premium > basic
        tiers_to_check = []
        if tier == "pro":
            tiers_to_check = ["pro", "premium", "basic"]
        elif tier == "premium":
            tiers_to_check = ["premium", "basic"]
        else:
            tiers_to_check = ["basic"]

        for t in tiers_to_check:
            alerts = await r.lrange(f"alerts:{t}", 0, limit - 1)
            all_alerts.extend([eval(a) for a in alerts])  # Safe since we control the data

        # Sort by score and return top N
        all_alerts.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_alerts[:limit]

    async def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert generation statistics."""
        r = await self.get_redis()
        today = datetime.utcnow().strftime('%Y-%m-%d')

        stats = {}
        for tier in self.TIER_CONFIG:
            count = await r.get(f"alert_count:{tier}:{today}")
            stats[tier] = {
                "alerts_today": int(count) if count else 0,
                "max_daily": self.TIER_CONFIG[tier]["max_alerts_per_day"],
            }

        # Total recent alerts
        total_recent = await r.llen("recent_alerts")
        stats["total_recent"] = total_recent

        return stats


# Singleton instance
alert_generator = AlertGenerator()
