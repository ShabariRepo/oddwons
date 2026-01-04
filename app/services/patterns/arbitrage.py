import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from datetime import datetime

from .base import PatternDetector, PatternResult, PatternType, MarketData

logger = logging.getLogger(__name__)


class ArbitrageDetector(PatternDetector):
    """Detects arbitrage opportunities across platforms and related markets."""

    # Default thresholds
    DEFAULT_MIN_SPREAD = 0.03  # 3% minimum spread for arbitrage
    DEFAULT_TITLE_SIMILARITY = 0.7  # 70% title similarity for matching
    DEFAULT_MIN_LIQUIDITY = 1000  # Minimum liquidity for viable arbitrage

    async def detect(self, market: MarketData) -> List[PatternResult]:
        """Single market detection - not applicable for arbitrage."""
        return []

    async def detect_batch(self, markets: List[MarketData]) -> List[PatternResult]:
        """Detect arbitrage opportunities across multiple markets."""
        patterns = []

        # Group markets by platform
        kalshi_markets = [m for m in markets if m.platform == "kalshi"]
        poly_markets = [m for m in markets if m.platform == "polymarket"]

        # Cross-platform arbitrage
        cross_platform = self._detect_cross_platform_arbitrage(kalshi_markets, poly_markets)
        patterns.extend(cross_platform)

        # Related market arbitrage within each platform
        kalshi_related = self._detect_related_market_arbitrage(kalshi_markets)
        poly_related = self._detect_related_market_arbitrage(poly_markets)
        patterns.extend(kalshi_related)
        patterns.extend(poly_related)

        return patterns

    def _detect_cross_platform_arbitrage(
        self,
        kalshi_markets: List[MarketData],
        poly_markets: List[MarketData]
    ) -> List[PatternResult]:
        """Find arbitrage between Kalshi and Polymarket for same events."""
        patterns = []
        min_spread = self.get_config("min_spread", self.DEFAULT_MIN_SPREAD)
        similarity_threshold = self.get_config("title_similarity", self.DEFAULT_TITLE_SIMILARITY)

        for kalshi in kalshi_markets:
            for poly in poly_markets:
                # Check if markets are for the same event
                similarity = self._title_similarity(kalshi.title, poly.title)
                if similarity < similarity_threshold:
                    continue

                # Check for price discrepancy
                arb = self._calculate_arbitrage(kalshi, poly)
                if arb and arb["spread"] >= min_spread:
                    profit_pct = arb["spread"] * 100

                    patterns.append(PatternResult(
                        pattern_type=PatternType.CROSS_PLATFORM_ARB,
                        market_id=kalshi.market_id,
                        confidence_score=min(100, 70 + profit_pct * 2),
                        profit_potential=min(100, profit_pct * 5),
                        time_sensitivity=5,  # Arbitrage is very time-sensitive
                        risk_level=2,  # Lower risk since it's hedged
                        description=f"Cross-platform arbitrage: {profit_pct:.1f}% spread",
                        action_suggestion=f"Buy {arb['buy_side']} on {arb['buy_platform']} at {arb['buy_price']:.2f}, "
                                          f"sell {arb['sell_side']} on {arb['sell_platform']} at {arb['sell_price']:.2f}. "
                                          f"Potential profit: {profit_pct:.1f}%",
                        data={
                            "kalshi_market": kalshi.market_id,
                            "polymarket_market": poly.market_id,
                            "kalshi_yes_price": kalshi.yes_price,
                            "polymarket_yes_price": poly.yes_price,
                            "spread": arb["spread"],
                            "profit_pct": profit_pct,
                            "buy_platform": arb["buy_platform"],
                            "buy_price": arb["buy_price"],
                            "sell_platform": arb["sell_platform"],
                            "sell_price": arb["sell_price"],
                            "title_similarity": similarity,
                        },
                        related_markets=[poly.market_id],
                    ))

        return patterns

    def _detect_related_market_arbitrage(self, markets: List[MarketData]) -> List[PatternResult]:
        """Find arbitrage in related/correlated markets within a platform."""
        patterns = []

        # Look for markets that should have correlated prices
        # e.g., "Will X win?" and "Will X lose?" should sum to ~1.0

        for i, m1 in enumerate(markets):
            for m2 in markets[i + 1:]:
                # Check for inverse relationship
                inverse = self._check_inverse_relationship(m1, m2)
                if inverse:
                    patterns.append(inverse)

                # Check for subset relationship (e.g., "Win primary" vs "Win election")
                subset = self._check_subset_relationship(m1, m2)
                if subset:
                    patterns.append(subset)

        return patterns

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two market titles."""
        # Normalize titles
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        # Use sequence matcher for fuzzy matching
        return SequenceMatcher(None, t1, t2).ratio()

    def _calculate_arbitrage(
        self,
        market1: MarketData,
        market2: MarketData
    ) -> Optional[Dict[str, Any]]:
        """Calculate arbitrage opportunity between two markets."""
        if not market1.yes_price or not market2.yes_price:
            return None

        p1_yes = market1.yes_price
        p2_yes = market2.yes_price

        # For same event: if one has higher YES, buy YES there, NO on the other
        # Arbitrage exists if: p1_yes + (1 - p2_yes) < 1 (or vice versa)
        # This means: p1_yes < p2_yes (buy YES on p1, NO on p2)

        if p1_yes < p2_yes:
            spread = p2_yes - p1_yes
            return {
                "spread": spread,
                "buy_platform": market1.platform,
                "buy_side": "YES",
                "buy_price": p1_yes,
                "sell_platform": market2.platform,
                "sell_side": "YES",  # Selling YES = buying NO effectively
                "sell_price": p2_yes,
            }
        elif p2_yes < p1_yes:
            spread = p1_yes - p2_yes
            return {
                "spread": spread,
                "buy_platform": market2.platform,
                "buy_side": "YES",
                "buy_price": p2_yes,
                "sell_platform": market1.platform,
                "sell_side": "YES",
                "sell_price": p1_yes,
            }

        return None

    def _check_inverse_relationship(
        self,
        m1: MarketData,
        m2: MarketData
    ) -> Optional[PatternResult]:
        """Check if two markets are inverses that should sum to 1."""
        if not m1.yes_price or not m2.yes_price:
            return None

        # Check for inverse keyword patterns
        inverse_pairs = [
            ("win", "lose"),
            ("yes", "no"),
            ("above", "below"),
            ("over", "under"),
            ("before", "after"),
        ]

        t1 = m1.title.lower()
        t2 = m2.title.lower()

        is_inverse = False
        for w1, w2 in inverse_pairs:
            if (w1 in t1 and w2 in t2) or (w2 in t1 and w1 in t2):
                # Check if rest of title is similar
                base_similarity = SequenceMatcher(
                    None,
                    t1.replace(w1, "").replace(w2, ""),
                    t2.replace(w1, "").replace(w2, "")
                ).ratio()
                if base_similarity > 0.6:
                    is_inverse = True
                    break

        if not is_inverse:
            return None

        # For inverse markets: YES1 + YES2 should ≈ 1.0
        sum_prices = m1.yes_price + m2.yes_price
        deviation = abs(sum_prices - 1.0)

        if deviation > 0.05:  # More than 5% deviation = opportunity
            profit_pct = deviation * 100

            if sum_prices < 1.0:
                action = "Buy YES on both markets"
            else:
                action = "Sell YES on both markets (buy NO)"

            return PatternResult(
                pattern_type=PatternType.RELATED_MARKET_ARB,
                market_id=m1.market_id,
                confidence_score=min(100, 60 + profit_pct * 3),
                profit_potential=min(100, profit_pct * 4),
                time_sensitivity=4,
                risk_level=2,
                description=f"Inverse market mispricing: {profit_pct:.1f}% deviation",
                action_suggestion=f"{action}. Sum of YES prices is {sum_prices:.2f} instead of 1.0. "
                                  f"Guaranteed profit of {profit_pct:.1f}% if markets are truly inverse.",
                data={
                    "market1_price": m1.yes_price,
                    "market2_price": m2.yes_price,
                    "sum": sum_prices,
                    "deviation": deviation,
                    "market1_title": m1.title,
                    "market2_title": m2.title,
                },
                related_markets=[m2.market_id],
            )

        return None

    def _check_subset_relationship(
        self,
        m1: MarketData,
        m2: MarketData
    ) -> Optional[PatternResult]:
        """Check if one market is a subset of another (should have lower probability)."""
        if not m1.yes_price or not m2.yes_price:
            return None

        # Subset indicators: "and", "both", specific vs general
        t1 = m1.title.lower()
        t2 = m2.title.lower()

        # Check if one is clearly more specific
        specificity_keywords = ["and", "both", "all", "every"]

        t1_specific = any(kw in t1 for kw in specificity_keywords)
        t2_specific = any(kw in t2 for kw in specificity_keywords)

        if t1_specific == t2_specific:
            return None  # Can't determine subset relationship

        if t1_specific:
            subset, superset = m1, m2
        else:
            subset, superset = m2, m1

        # Subset should have lower probability
        if subset.yes_price > superset.yes_price:
            deviation = subset.yes_price - superset.yes_price
            profit_pct = deviation * 100

            return PatternResult(
                pattern_type=PatternType.RELATED_MARKET_ARB,
                market_id=subset.market_id,
                confidence_score=min(100, 55 + profit_pct * 2),
                profit_potential=min(100, profit_pct * 3),
                time_sensitivity=3,
                risk_level=3,
                description=f"Subset market mispricing: {profit_pct:.1f}% deviation",
                action_suggestion=f"More specific market priced higher than general market. "
                                  f"Consider selling YES on '{subset.title[:50]}...' "
                                  f"or buying YES on '{superset.title[:50]}...'",
                data={
                    "subset_market": subset.market_id,
                    "subset_price": subset.yes_price,
                    "superset_market": superset.market_id,
                    "superset_price": superset.yes_price,
                    "deviation": deviation,
                },
                related_markets=[superset.market_id if subset == m1 else subset.market_id],
            )

        return None
