import logging
from typing import List, Dict, Any, Optional
from statistics import mean, stdev
from datetime import datetime, timedelta

from .base import PatternDetector, PatternResult, PatternType, MarketData

logger = logging.getLogger(__name__)


class VolumePatternDetector(PatternDetector):
    """Detects volume-based patterns in market data."""

    # Default thresholds
    DEFAULT_SPIKE_MULTIPLIER = 3.0  # 3x normal volume = spike
    DEFAULT_MIN_HISTORY_POINTS = 5
    DEFAULT_DIVERGENCE_THRESHOLD = 0.3  # 30% divergence

    async def detect(self, market: MarketData) -> List[PatternResult]:
        """Detect volume patterns in a single market."""
        patterns = []

        # Check for volume spike
        spike = self._detect_volume_spike(market)
        if spike:
            patterns.append(spike)

        # Check for volume divergence (volume up, price stable)
        divergence = self._detect_volume_divergence(market)
        if divergence:
            patterns.append(divergence)

        # Check for unusual flow direction
        flow = self._detect_unusual_flow(market)
        if flow:
            patterns.append(flow)

        return patterns

    async def detect_batch(self, markets: List[MarketData]) -> List[PatternResult]:
        """Detect volume patterns across multiple markets."""
        all_patterns = []
        for market in markets:
            try:
                patterns = await self.detect(market)
                all_patterns.extend(patterns)
            except Exception as e:
                logger.warning(f"Error detecting patterns for {market.market_id}: {e}")
        return all_patterns

    def _detect_volume_spike(self, market: MarketData) -> Optional[PatternResult]:
        """Detect sudden volume spikes (>3x normal)."""
        if not market.volume_history:
            return None

        min_points = self.get_config("min_history_points", self.DEFAULT_MIN_HISTORY_POINTS)
        if len(market.volume_history) < min_points:
            return None

        # Calculate baseline (exclude last point)
        volumes = [h.get("volume", 0) for h in market.volume_history[:-1] if h.get("volume")]
        if not volumes:
            return None

        avg_volume = mean(volumes)
        if avg_volume == 0:
            return None

        # Get current volume
        current_volume = market.volume or market.volume_history[-1].get("volume", 0)
        if not current_volume:
            return None

        # Calculate spike ratio
        spike_multiplier = self.get_config("spike_multiplier", self.DEFAULT_SPIKE_MULTIPLIER)
        ratio = current_volume / avg_volume

        if ratio >= spike_multiplier:
            # Calculate confidence based on how far above threshold
            confidence = min(100, 50 + (ratio - spike_multiplier) * 10)

            # Higher volume spikes = higher profit potential
            profit_potential = min(100, 40 + ratio * 5)

            # Check if volume is accompanied by price movement
            price_moved = self._check_price_movement(market)
            if price_moved:
                confidence += 10
                profit_potential += 10

            return PatternResult(
                pattern_type=PatternType.VOLUME_SPIKE,
                market_id=market.market_id,
                confidence_score=min(100, confidence),
                profit_potential=min(100, profit_potential),
                time_sensitivity=4,  # Volume spikes are time-sensitive
                risk_level=3,
                description=f"Volume spike detected: {ratio:.1f}x normal volume",
                action_suggestion=f"Investigate {market.title} - unusual activity detected. "
                                  f"Current volume is {ratio:.1f}x the average.",
                data={
                    "current_volume": current_volume,
                    "average_volume": avg_volume,
                    "spike_ratio": ratio,
                    "price_moved": price_moved,
                },
            )

        return None

    def _detect_volume_divergence(self, market: MarketData) -> Optional[PatternResult]:
        """Detect volume/price divergence (volume up but price stable)."""
        if len(market.volume_history) < 3 or len(market.price_history) < 3:
            return None

        # Get recent volume trend
        recent_volumes = [h.get("volume", 0) for h in market.volume_history[-5:] if h.get("volume")]
        if len(recent_volumes) < 3:
            return None

        volume_change = (recent_volumes[-1] - recent_volumes[0]) / (recent_volumes[0] + 0.001)

        # Get recent price trend
        recent_prices = [h.get("yes_price", 0) for h in market.price_history[-5:] if h.get("yes_price")]
        if len(recent_prices) < 3:
            return None

        price_change = abs(recent_prices[-1] - recent_prices[0]) / (recent_prices[0] + 0.001)

        threshold = self.get_config("divergence_threshold", self.DEFAULT_DIVERGENCE_THRESHOLD)

        # Volume up significantly but price stable
        if volume_change > threshold and price_change < 0.05:
            confidence = min(100, 50 + volume_change * 50)

            return PatternResult(
                pattern_type=PatternType.VOLUME_DIVERGENCE,
                market_id=market.market_id,
                confidence_score=confidence,
                profit_potential=60,  # Moderate profit potential
                time_sensitivity=3,
                risk_level=2,
                description=f"Volume divergence: volume up {volume_change*100:.1f}% but price stable",
                action_suggestion="Large volume with stable price may indicate accumulation. "
                                  "Watch for upcoming price movement.",
                data={
                    "volume_change_pct": volume_change * 100,
                    "price_change_pct": price_change * 100,
                    "interpretation": "accumulation" if recent_prices[-1] < 0.5 else "distribution",
                },
            )

        return None

    def _detect_unusual_flow(self, market: MarketData) -> Optional[PatternResult]:
        """Detect unusual directional betting flow."""
        if not market.volume_history or len(market.volume_history) < 10:
            return None

        # Calculate volume acceleration
        volumes = [h.get("volume", 0) for h in market.volume_history if h.get("volume")]
        if len(volumes) < 10:
            return None

        # Compare recent vs historical
        recent_avg = mean(volumes[-3:])
        historical_avg = mean(volumes[:-3])

        if historical_avg == 0:
            return None

        acceleration = (recent_avg - historical_avg) / historical_avg

        # Significant acceleration indicates unusual flow
        if acceleration > 0.5:  # 50% acceleration
            # Check price direction for flow direction
            price_direction = "unknown"
            if market.price_history:
                recent_price = market.price_history[-1].get("yes_price", 0.5)
                old_price = market.price_history[-min(3, len(market.price_history))].get("yes_price", 0.5)
                if recent_price > old_price + 0.02:
                    price_direction = "bullish (YES)"
                elif recent_price < old_price - 0.02:
                    price_direction = "bearish (NO)"

            return PatternResult(
                pattern_type=PatternType.UNUSUAL_FLOW,
                market_id=market.market_id,
                confidence_score=min(100, 50 + acceleration * 30),
                profit_potential=55,
                time_sensitivity=3,
                risk_level=3,
                description=f"Unusual betting flow detected: {acceleration*100:.1f}% acceleration",
                action_suggestion=f"Significant increase in betting activity. Flow appears {price_direction}.",
                data={
                    "acceleration_pct": acceleration * 100,
                    "recent_avg_volume": recent_avg,
                    "historical_avg_volume": historical_avg,
                    "flow_direction": price_direction,
                },
            )

        return None

    def _check_price_movement(self, market: MarketData) -> bool:
        """Check if there's been recent price movement."""
        if not market.price_history or len(market.price_history) < 2:
            return False

        recent = market.price_history[-1].get("yes_price", 0)
        previous = market.price_history[-2].get("yes_price", 0)

        if previous == 0:
            return False

        change = abs(recent - previous) / previous
        return change > 0.05  # 5% price change
