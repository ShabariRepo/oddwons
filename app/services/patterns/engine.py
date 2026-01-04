import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.market import Market, MarketSnapshot, Pattern as PatternModel, Platform
from app.models.ai_insight import AIInsight, ArbitrageOpportunity, DailyDigest
from app.core.database import AsyncSessionLocal
from app.services.ai_agent import ai_agent

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

    async def run_full_analysis(self, with_ai: bool = True) -> Dict[str, Any]:
        """Run complete analysis cycle: load, detect, AI analyze, save."""
        async with AsyncSessionLocal() as session:
            # Load market data
            markets = await self.load_market_data(session)

            # Run rule-based detection
            patterns = await self.run_detection(markets, session)

            # Save rule-based patterns
            saved = await self.save_patterns(patterns, session)

            # AI analysis on promising patterns
            ai_insights_saved = 0
            if with_ai and ai_agent.is_enabled():
                ai_insights_saved = await self.run_ai_analysis(patterns, markets, session)

            # Get top opportunities
            top_opportunities = self.scorer.get_top_opportunities(patterns, limit=10)

            # Categorize patterns
            categories = self.scorer.categorize(patterns)

            return {
                "total_markets_analyzed": len(markets),
                "total_patterns_detected": len(patterns),
                "patterns_saved": saved,
                "ai_insights_saved": ai_insights_saved,
                "top_opportunities": top_opportunities,
                "by_category": {
                    k: len(v) for k, v in categories.items()
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def run_ai_analysis(
        self,
        patterns: List[PatternResult],
        markets: List[MarketData],
        session: AsyncSession
    ) -> int:
        """
        Run AI analysis on detected patterns.
        This is where the REAL value is created.
        """
        if not ai_agent.is_enabled():
            logger.warning("AI agent not enabled - skipping AI analysis")
            return 0

        saved = 0

        # Analyze top patterns (those worth looking at)
        promising_patterns = [p for p in patterns if p.confidence_score and p.confidence_score > 50]
        logger.info(f"Running AI analysis on {len(promising_patterns)} promising patterns")

        for pattern in promising_patterns[:20]:  # Limit to avoid API overload
            try:
                # Find the market data for this pattern
                market_data = next(
                    (m for m in markets if m.market_id == pattern.market_id),
                    None
                )
                if not market_data:
                    continue

                # Convert to dict for AI
                market_dict = {
                    "market_id": market_data.market_id,
                    "platform": market_data.platform,
                    "title": market_data.title,
                    "yes_price": market_data.yes_price,
                    "no_price": market_data.no_price,
                    "volume": market_data.volume,
                    "price_history": market_data.price_history[-5:] if market_data.price_history else [],
                }

                pattern_dict = {
                    "pattern_type": pattern.pattern_type.value,
                    "description": pattern.description,
                    "confidence_score": pattern.confidence_score,
                    "profit_potential": pattern.profit_potential,
                }

                # Get AI analysis
                ai_insight = await ai_agent.analyze_opportunity(market_dict, [pattern_dict])

                if ai_insight and ai_insight.get("confidence_score", 0) > 40:
                    # Save to database
                    await self.save_ai_insight(ai_insight, pattern, session)
                    saved += 1

            except Exception as e:
                logger.error(f"AI analysis failed for {pattern.market_id}: {e}")

        # Run cross-platform arbitrage analysis
        try:
            kalshi_markets = [m for m in markets if m.platform == "kalshi"]
            poly_markets = [m for m in markets if m.platform == "polymarket"]

            if kalshi_markets and poly_markets:
                kalshi_dicts = [{"market_id": m.market_id, "title": m.title, "yes_price": m.yes_price, "volume": m.volume} for m in kalshi_markets[:30]]
                poly_dicts = [{"market_id": m.market_id, "title": m.title, "yes_price": m.yes_price, "volume": m.volume} for m in poly_markets[:30]]

                arb_result = await ai_agent.analyze_cross_platform_arbitrage(kalshi_dicts, poly_dicts)
                if arb_result:
                    arb_saved = await self.save_arbitrage_opportunities(arb_result, session)
                    logger.info(f"Saved {arb_saved} arbitrage opportunities")

        except Exception as e:
            logger.error(f"Arbitrage analysis failed: {e}")

        await session.commit()
        logger.info(f"AI analysis complete: {saved} insights saved")
        return saved

    async def save_ai_insight(
        self,
        ai_insight: Dict[str, Any],
        pattern: PatternResult,
        session: AsyncSession
    ) -> None:
        """Save an AI insight to the database."""
        try:
            insight = AIInsight(
                market_id=pattern.market_id,
                platform=pattern.data.get("platform", "unknown") if pattern.data else "unknown",
                pattern_type=pattern.pattern_type.value,
                recommendation=ai_insight.get("recommendation", "CAUTION"),
                confidence_score=ai_insight.get("confidence_score", 0),
                one_liner=ai_insight.get("one_liner", ""),
                reasoning=ai_insight.get("reasoning", ""),
                risk_factors=ai_insight.get("risk_factors", []),
                suggested_position=ai_insight.get("suggested_position", "WAIT"),
                edge_explanation=ai_insight.get("edge_explanation", ""),
                time_sensitivity=ai_insight.get("time_sensitivity", "DAYS"),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                status="active"
            )
            session.add(insight)
            logger.debug(f"Saved AI insight for {pattern.market_id}")
        except Exception as e:
            logger.error(f"Failed to save AI insight: {e}")

    async def save_arbitrage_opportunities(
        self,
        arb_result: Dict[str, Any],
        session: AsyncSession
    ) -> int:
        """Save arbitrage opportunities to database."""
        saved = 0
        opportunities = arb_result.get("arbitrage_opportunities", [])

        for opp in opportunities:
            try:
                arb = ArbitrageOpportunity(
                    opportunity_type=opp.get("type", "CROSS_PLATFORM"),
                    description=opp.get("description", ""),
                    kalshi_market_id=opp.get("kalshi_market"),
                    polymarket_market_id=opp.get("polymarket_market"),
                    edge_percentage=float(opp.get("edge_percentage", "0").replace("%", "")) if opp.get("edge_percentage") else None,
                    execution_steps=opp.get("execution_steps", []),
                    risks=opp.get("risks", []),
                    confidence_score=opp.get("confidence", 0),
                    expires_at=datetime.utcnow() + timedelta(hours=12),
                    status="active"
                )
                session.add(arb)
                saved += 1
            except Exception as e:
                logger.error(f"Failed to save arbitrage opportunity: {e}")

        return saved

    async def generate_daily_digest(self, tier: str = "basic") -> Optional[Dict[str, Any]]:
        """Generate daily digest using AI agent."""
        if not ai_agent.is_enabled():
            return None

        async with AsyncSessionLocal() as session:
            # Get recent AI insights
            result = await session.execute(
                select(AIInsight)
                .where(AIInsight.status == "active")
                .where(AIInsight.created_at > datetime.utcnow() - timedelta(hours=24))
                .order_by(AIInsight.confidence_score.desc())
                .limit(50)
            )
            insights = result.scalars().all()

            if not insights:
                logger.info("No recent insights for digest")
                return None

            # Convert to dicts for AI
            opportunities = []
            for i in insights:
                opportunities.append({
                    "market_id": i.market_id,
                    "platform": i.platform,
                    "recommendation": i.recommendation,
                    "confidence_score": i.confidence_score,
                    "one_liner": i.one_liner,
                    "reasoning": i.reasoning,
                    "time_sensitivity": i.time_sensitivity,
                })

            # Generate digest with AI
            digest = await ai_agent.generate_daily_digest(opportunities)

            if digest:
                # Save digest
                daily = DailyDigest(
                    digest_date=datetime.utcnow().date(),
                    tier=tier,
                    top_picks=digest.get("top_picks", []),
                    avoid_list=digest.get("avoid_list", []),
                    market_sentiment=digest.get("market_sentiment", ""),
                    arbitrage_opportunities=digest.get("arbitrage_opportunities", []),
                    watchlist=digest.get("watchlist", []),
                )
                session.add(daily)
                await session.commit()
                logger.info(f"Generated and saved daily digest for tier {tier}")

            return digest

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
