import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.market import Market, MarketSnapshot, Pattern as PatternModel, Platform
from app.core.database import AsyncSessionLocal

from .base import PatternResult, MarketData
from .volume import VolumePatternDetector
from .price import PricePatternDetector
from .arbitrage import ArbitrageDetector
from .scoring import PatternScorer

logger = logging.getLogger(__name__)


class PatternEngine:
    """Main engine for running pattern detection across all detectors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize detectors
        self.volume_detector = VolumePatternDetector(config)
        self.price_detector = PricePatternDetector(config)
        self.arbitrage_detector = ArbitrageDetector(config)

        # Initialize scorer
        self.scorer = PatternScorer()

    async def load_market_data(
        self,
        session: AsyncSession,
        limit: int = 500,
        history_points: int = 20
    ) -> List[MarketData]:
        """Load market data with history from database."""
        # Get active markets
        result = await session.execute(
            select(Market)
            .where(Market.status == "active")
            .order_by(Market.volume.desc().nullslast())
            .limit(limit)
        )
        markets = result.scalars().all()

        market_data_list = []

        for market in markets:
            # Get price/volume history
            snapshot_result = await session.execute(
                select(MarketSnapshot)
                .where(MarketSnapshot.market_id == market.id)
                .order_by(MarketSnapshot.timestamp.desc())
                .limit(history_points)
            )
            snapshots = list(reversed(snapshot_result.scalars().all()))

            price_history = []
            volume_history = []

            for s in snapshots:
                price_history.append({
                    "yes_price": s.yes_price,
                    "no_price": s.no_price,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                })
                volume_history.append({
                    "volume": s.volume,
                    "volume_24h": s.volume_24h,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                })

            market_data = MarketData(
                market_id=market.id,
                platform=market.platform.value if isinstance(market.platform, Platform) else market.platform,
                title=market.title,
                yes_price=market.yes_price,
                no_price=market.no_price,
                volume=market.volume,
                best_bid=snapshots[-1].best_bid if snapshots else None,
                best_ask=snapshots[-1].best_ask if snapshots else None,
                spread=snapshots[-1].spread if snapshots else None,
                price_history=price_history,
                volume_history=volume_history,
            )
            market_data_list.append(market_data)

        logger.info(f"Loaded {len(market_data_list)} markets for pattern detection")
        return market_data_list

    async def run_detection(
        self,
        markets: Optional[List[MarketData]] = None,
        session: Optional[AsyncSession] = None
    ) -> List[PatternResult]:
        """Run all pattern detectors."""
        # Load data if not provided
        if markets is None:
            if session is None:
                async with AsyncSessionLocal() as session:
                    markets = await self.load_market_data(session)
            else:
                markets = await self.load_market_data(session)

        if not markets:
            logger.warning("No markets available for pattern detection")
            return []

        all_patterns = []

        # Run volume detection
        try:
            volume_patterns = await self.volume_detector.detect_batch(markets)
            all_patterns.extend(volume_patterns)
            logger.info(f"Volume detector found {len(volume_patterns)} patterns")
        except Exception as e:
            logger.error(f"Volume detection error: {e}")

        # Run price detection
        try:
            price_patterns = await self.price_detector.detect_batch(markets)
            all_patterns.extend(price_patterns)
            logger.info(f"Price detector found {len(price_patterns)} patterns")
        except Exception as e:
            logger.error(f"Price detection error: {e}")

        # Run arbitrage detection
        try:
            arb_patterns = await self.arbitrage_detector.detect_batch(markets)
            all_patterns.extend(arb_patterns)
            logger.info(f"Arbitrage detector found {len(arb_patterns)} patterns")
        except Exception as e:
            logger.error(f"Arbitrage detection error: {e}")

        # Deduplicate patterns (same market, same type within short time)
        all_patterns = self._deduplicate(all_patterns)

        # Score and rank
        all_patterns = self.scorer.rank(all_patterns)

        logger.info(f"Total patterns detected: {len(all_patterns)}")
        return all_patterns

    async def save_patterns(
        self,
        patterns: List[PatternResult],
        session: AsyncSession
    ) -> int:
        """Save detected patterns to database."""
        saved = 0

        for pattern in patterns:
            try:
                stmt = insert(PatternModel).values(
                    market_id=pattern.market_id,
                    pattern_type=pattern.pattern_type.value,
                    description=pattern.description,
                    confidence_score=pattern.confidence_score,
                    profit_potential=pattern.profit_potential,
                    time_sensitivity=pattern.time_sensitivity,
                    risk_level=pattern.risk_level,
                    data=pattern.data,
                    status="active",
                    detected_at=pattern.detected_at,
                    expires_at=pattern.expires_at,
                )
                await session.execute(stmt)
                saved += 1
            except Exception as e:
                logger.warning(f"Failed to save pattern: {e}")

        await session.commit()
        logger.info(f"Saved {saved} patterns to database")
        return saved

    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete analysis cycle: load, detect, save."""
        async with AsyncSessionLocal() as session:
            # Load market data
            markets = await self.load_market_data(session)

            # Run detection
            patterns = await self.run_detection(markets, session)

            # Save to database
            saved = await self.save_patterns(patterns, session)

            # Get top opportunities
            top_opportunities = self.scorer.get_top_opportunities(patterns, limit=10)

            # Categorize patterns
            categories = self.scorer.categorize(patterns)

            return {
                "total_markets_analyzed": len(markets),
                "total_patterns_detected": len(patterns),
                "patterns_saved": saved,
                "top_opportunities": top_opportunities,
                "by_category": {
                    k: len(v) for k, v in categories.items()
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _deduplicate(self, patterns: List[PatternResult]) -> List[PatternResult]:
        """Remove duplicate patterns (same market + type)."""
        seen = set()
        unique = []

        for p in patterns:
            key = (p.market_id, p.pattern_type.value)
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique


# Singleton instance
pattern_engine = PatternEngine()
