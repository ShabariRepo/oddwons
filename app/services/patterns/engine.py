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

    def _infer_category(self, title: str) -> str:
        """Infer category from market title using keywords."""
        title_lower = title.lower()

        # Category keyword mappings
        categories = {
            "politics": ["trump", "biden", "election", "president", "senate", "congress", "vote", "governor", "democrat", "republican", "gop", "political", "white house"],
            "sports": ["nfl", "nba", "mlb", "nhl", "soccer", "football", "basketball", "baseball", "hockey", "tennis", "golf", "ufc", "boxing", "game", "match", "championship", "super bowl", "playoffs"],
            "crypto": ["bitcoin", "btc", "ethereum", "eth", "crypto", "solana", "sol", "xrp", "dogecoin", "blockchain"],
            "finance": ["stock", "s&p", "nasdaq", "fed", "interest rate", "inflation", "gdp", "unemployment", "market cap", "ipo"],
            "entertainment": ["oscar", "grammy", "emmy", "movie", "film", "tv show", "celebrity", "netflix", "streaming"],
            "tech": ["ai", "apple", "google", "microsoft", "amazon", "meta", "openai", "chatgpt", "tesla", "spacex"],
            "weather": ["hurricane", "temperature", "weather", "climate", "storm", "flood"],
            "world": ["ukraine", "russia", "china", "war", "nato", "un", "europe", "asia"],
        }

        for category, keywords in categories.items():
            if any(kw in title_lower for kw in keywords):
                return category

        return "other"

    async def run_ai_analysis(
        self,
        patterns: List[PatternResult],
        markets: List[MarketData],
        session: AsyncSession
    ) -> int:
        """
        Run AI analysis on detected patterns, grouped by category.
        This keeps AI context focused for better analysis quality.
        """
        if not ai_agent.is_enabled():
            logger.warning("AI agent not enabled - skipping AI analysis")
            return 0

        saved = 0

        # Group markets by category
        market_by_category: Dict[str, List[Dict[str, Any]]] = {}
        pattern_by_category: Dict[str, List[Dict[str, Any]]] = {}

        for market in markets:
            category = self._infer_category(market.title or "")
            if category not in market_by_category:
                market_by_category[category] = []

            market_by_category[category].append({
                "market_id": market.market_id,
                "platform": market.platform,
                "title": market.title,
                "yes_price": market.yes_price,
                "no_price": market.no_price,
                "volume": market.volume,
                "price_history": market.price_history[-5:] if market.price_history else [],
            })

        # Group patterns by category
        promising_patterns = [p for p in patterns if p.confidence_score and p.confidence_score > 50]
        for pattern in promising_patterns:
            # Find the market title for this pattern
            market = next((m for m in markets if m.market_id == pattern.market_id), None)
            title = market.title if market else ""
            category = self._infer_category(title)

            if category not in pattern_by_category:
                pattern_by_category[category] = []

            pattern_by_category[category].append({
                "market_id": pattern.market_id,
                "pattern_type": pattern.pattern_type.value,
                "description": pattern.description,
                "confidence_score": pattern.confidence_score,
                "profit_potential": pattern.profit_potential,
            })

        # Analyze each category separately (better context = better analysis)
        categories_analyzed = 0
        for category, category_markets in market_by_category.items():
            if not category_markets:
                continue

            # Only analyze categories with patterns or high volume
            category_patterns = pattern_by_category.get(category, [])
            if not category_patterns and len(category_markets) < 5:
                continue

            try:
                logger.info(f"Analyzing category '{category}': {len(category_markets)} markets, {len(category_patterns)} patterns")

                result = await ai_agent.analyze_category_batch(
                    category=category,
                    markets=category_markets,
                    patterns=category_patterns
                )

                if result and result.get("opportunities"):
                    for opp in result["opportunities"]:
                        if opp.get("confidence_score", 0) > 40:
                            # Find the pattern for this market if any
                            pattern = next(
                                (p for p in promising_patterns if p.market_id == opp.get("market_id")),
                                None
                            )
                            if pattern:
                                await self.save_ai_insight(opp, pattern, session)
                                saved += 1
                            else:
                                # Create a synthetic insight even without pattern match
                                await self.save_category_insight(opp, category, session)
                                saved += 1

                categories_analyzed += 1

            except Exception as e:
                logger.error(f"Category analysis failed for {category}: {e}")

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
        logger.info(f"AI analysis complete: {saved} insights saved across {categories_analyzed} categories")
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

    async def save_category_insight(
        self,
        opp: Dict[str, Any],
        category: str,
        session: AsyncSession
    ) -> None:
        """Save an AI insight from category analysis (no pattern required)."""
        try:
            insight = AIInsight(
                market_id=opp.get("market_id", "unknown"),
                platform="unknown",  # Will be determined from market lookup
                pattern_type=f"category_{category}",
                recommendation=opp.get("recommendation", "CAUTION"),
                confidence_score=opp.get("confidence_score", 0),
                one_liner=opp.get("one_liner", ""),
                reasoning=opp.get("reasoning", ""),
                risk_factors=opp.get("risk_factors", []),
                suggested_position=opp.get("suggested_position", "WAIT"),
                edge_explanation=opp.get("edge_explanation", ""),
                time_sensitivity=opp.get("time_sensitivity", "DAYS"),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                status="active"
            )
            session.add(insight)
            logger.debug(f"Saved category insight for {opp.get('market_id')} ({category})")
        except Exception as e:
            logger.error(f"Failed to save category insight: {e}")

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
