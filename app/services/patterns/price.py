import logging
from typing import List, Dict, Any, Optional
from statistics import mean, stdev
from datetime import datetime

from .base import PatternDetector, PatternResult, PatternType, MarketData

logger = logging.getLogger(__name__)


class PricePatternDetector(PatternDetector):
    """Detects price-based patterns in market data."""

    # Default thresholds
    DEFAULT_RAPID_CHANGE_THRESHOLD = 0.10  # 10% change
    DEFAULT_RAPID_CHANGE_HOURS = 1
    DEFAULT_REVERSAL_THRESHOLD = 0.15  # 15% reversal
    DEFAULT_SUPPORT_RESISTANCE_TOUCHES = 3

    async def detect(self, market: MarketData) -> List[PatternResult]:
        """Detect price patterns in a single market."""
        patterns = []

        # Check for rapid price change
        rapid = self._detect_rapid_price_change(market)
        if rapid:
            patterns.append(rapid)

        # Check for trend reversal
        reversal = self._detect_trend_reversal(market)
        if reversal:
            patterns.append(reversal)

        # Check for support/resistance breaks
        breaks = self._detect_support_resistance_break(market)
        patterns.extend(breaks)

        return patterns

    async def detect_batch(self, markets: List[MarketData]) -> List[PatternResult]:
        """Detect price patterns across multiple markets."""
        all_patterns = []
        for market in markets:
            try:
                patterns = await self.detect(market)
                all_patterns.extend(patterns)
            except Exception as e:
                logger.warning(f"Error detecting price patterns for {market.market_id}: {e}")
        return all_patterns

    def _detect_rapid_price_change(self, market: MarketData) -> Optional[PatternResult]:
        """Detect rapid price changes (>10% in 1 hour)."""
        if not market.price_history or len(market.price_history) < 2:
            return None

        threshold = self.get_config("rapid_change_threshold", self.DEFAULT_RAPID_CHANGE_THRESHOLD)

        # Get current and recent prices
        current = market.yes_price or market.price_history[-1].get("yes_price")
        if not current:
            return None

        # Look for change over recent snapshots (assuming ~15 min intervals, 4 = 1 hour)
        lookback = min(4, len(market.price_history) - 1)
        if lookback < 1:
            return None

        old_price = market.price_history[-(lookback + 1)].get("yes_price")
        if not old_price or old_price == 0:
            return None

        change = (current - old_price) / old_price
        abs_change = abs(change)

        if abs_change >= threshold:
            direction = "up" if change > 0 else "down"
            confidence = min(100, 60 + abs_change * 100)

            # Larger moves = higher profit potential but also risk
            profit_potential = min(100, 50 + abs_change * 150)
            risk_level = 3 if abs_change < 0.2 else 4

            return PatternResult(
                pattern_type=PatternType.RAPID_PRICE_CHANGE,
                market_id=market.market_id,
                confidence_score=confidence,
                profit_potential=profit_potential,
                time_sensitivity=5,  # Very time-sensitive
                risk_level=risk_level,
                description=f"Rapid price movement: {direction} {abs_change*100:.1f}%",
                action_suggestion=f"Price moved {direction} {abs_change*100:.1f}% recently. "
                                  f"{'Consider YES position' if change < 0 else 'Consider NO position'} "
                                  f"if you believe this is an overreaction.",
                data={
                    "current_price": current,
                    "previous_price": old_price,
                    "change_pct": change * 100,
                    "direction": direction,
                    "lookback_periods": lookback,
                },
            )

        return None

    def _detect_trend_reversal(self, market: MarketData) -> Optional[PatternResult]:
        """Detect momentum shifts / trend reversals."""
        if not market.price_history or len(market.price_history) < 8:
            return None

        prices = [h.get("yes_price") for h in market.price_history if h.get("yes_price")]
        if len(prices) < 8:
            return None

        threshold = self.get_config("reversal_threshold", self.DEFAULT_REVERSAL_THRESHOLD)

        # Calculate trend in first half vs second half
        mid = len(prices) // 2
        first_half = prices[:mid]
        second_half = prices[mid:]

        first_trend = (first_half[-1] - first_half[0]) / (first_half[0] + 0.001)
        second_trend = (second_half[-1] - second_half[0]) / (second_half[0] + 0.001)

        # Reversal = opposite trends with significant magnitude
        if first_trend * second_trend < 0:  # Opposite signs
            reversal_magnitude = abs(first_trend) + abs(second_trend)

            if reversal_magnitude >= threshold:
                was_direction = "up" if first_trend > 0 else "down"
                now_direction = "up" if second_trend > 0 else "down"

                confidence = min(100, 50 + reversal_magnitude * 100)

                return PatternResult(
                    pattern_type=PatternType.TREND_REVERSAL,
                    market_id=market.market_id,
                    confidence_score=confidence,
                    profit_potential=65,
                    time_sensitivity=3,
                    risk_level=3,
                    description=f"Trend reversal: was trending {was_direction}, now trending {now_direction}",
                    action_suggestion=f"Market momentum has shifted from {was_direction} to {now_direction}. "
                                      f"Consider positioning for the new trend direction.",
                    data={
                        "first_half_trend": first_trend * 100,
                        "second_half_trend": second_trend * 100,
                        "reversal_magnitude": reversal_magnitude * 100,
                        "current_price": prices[-1],
                    },
                )

        return None

    def _detect_support_resistance_break(self, market: MarketData) -> List[PatternResult]:
        """Detect breaks of support or resistance levels."""
        patterns = []

        if not market.price_history or len(market.price_history) < 10:
            return patterns

        prices = [h.get("yes_price") for h in market.price_history if h.get("yes_price")]
        if len(prices) < 10:
            return patterns

        current = prices[-1]
        historical = prices[:-1]

        # Find support and resistance levels
        support, resistance = self._find_support_resistance(historical)

        # Check for support break
        if support and current < support * 0.98:  # Break below by 2%
            patterns.append(PatternResult(
                pattern_type=PatternType.SUPPORT_BREAK,
                market_id=market.market_id,
                confidence_score=70,
                profit_potential=60,
                time_sensitivity=4,
                risk_level=4,
                description=f"Support break: price ({current:.2f}) below support ({support:.2f})",
                action_suggestion="Support level broken. This often indicates further downside. "
                                  "Consider NO position with caution.",
                data={
                    "current_price": current,
                    "support_level": support,
                    "break_pct": (support - current) / support * 100,
                },
            ))

        # Check for resistance break
        if resistance and current > resistance * 1.02:  # Break above by 2%
            patterns.append(PatternResult(
                pattern_type=PatternType.RESISTANCE_BREAK,
                market_id=market.market_id,
                confidence_score=70,
                profit_potential=60,
                time_sensitivity=4,
                risk_level=3,
                description=f"Resistance break: price ({current:.2f}) above resistance ({resistance:.2f})",
                action_suggestion="Resistance level broken. This often indicates further upside. "
                                  "Consider YES position.",
                data={
                    "current_price": current,
                    "resistance_level": resistance,
                    "break_pct": (current - resistance) / resistance * 100,
                },
            ))

        return patterns

    def _find_support_resistance(self, prices: List[float]) -> tuple:
        """Find support and resistance levels from price history."""
        if not prices:
            return None, None

        # Simple approach: find price levels that were touched multiple times
        min_touches = self.get_config("support_resistance_touches", self.DEFAULT_SUPPORT_RESISTANCE_TOUCHES)

        # Bucket prices into ranges
        price_min, price_max = min(prices), max(prices)
        if price_max == price_min:
            return None, None

        bucket_size = (price_max - price_min) / 20  # 20 buckets
        if bucket_size == 0:
            return None, None

        buckets = {}
        for p in prices:
            bucket = int((p - price_min) / bucket_size)
            buckets[bucket] = buckets.get(bucket, 0) + 1

        # Find most touched levels
        sorted_buckets = sorted(buckets.items(), key=lambda x: x[1], reverse=True)

        support = None
        resistance = None

        for bucket, count in sorted_buckets:
            if count < min_touches:
                continue

            level = price_min + (bucket + 0.5) * bucket_size
            current = prices[-1]

            if level < current and support is None:
                support = level
            elif level > current and resistance is None:
                resistance = level

            if support and resistance:
                break

        return support, resistance
