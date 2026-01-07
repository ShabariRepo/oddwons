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
from app.services.gemini_search import search_category_news

from .base import PatternResult, MarketData
from .volume import VolumePatternDetector
from .price import PricePatternDetector
from .arbitrage import ArbitrageDetector
from .scoring import PatternScorer
from app.services.alerts import alert_generator

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
        limit: int = 10000,
        history_points: int = 20,
        min_volume: float = 1000
    ) -> List[MarketData]:
        """Load market data with history from database.

        Args:
            limit: Max number of markets to load (default 10,000)
            history_points: Number of historical snapshots per market
            min_volume: Minimum volume threshold (default $1,000)
        """
        # Get active markets with minimum volume AND valid prices (not resolved)
        result = await session.execute(
            select(Market)
            .where(Market.status == "active")
            .where(Market.volume >= min_volume)
            .where(Market.yes_price > 0.02)   # Filter out resolved (0%)
            .where(Market.yes_price < 0.98)   # Filter out resolved (100%)
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

    async def run_full_analysis(self, with_ai: bool = True, min_volume: float = 1000) -> Dict[str, Any]:
        """Run complete analysis cycle: load, detect, AI analyze, save.

        Args:
            with_ai: Whether to run AI analysis (default True)
            min_volume: Minimum volume threshold for markets (default $1,000)
        """
        async with AsyncSessionLocal() as session:
            # Load ALL markets with volume > min_volume (default $1k)
            markets = await self.load_market_data(session, min_volume=min_volume)

            # Run rule-based detection
            patterns = await self.run_detection(markets, session)

            # Save rule-based patterns
            saved = await self.save_patterns(patterns, session)

            # Generate alerts from patterns (push to Redis for real-time alerts)
            alerts_generated = 0
            if patterns:
                try:
                    alerts = await alert_generator.generate_alerts(patterns, session)
                    alerts_generated = len(alerts)
                    logger.info(f"Generated {alerts_generated} alerts from {len(patterns)} patterns")
                except Exception as e:
                    logger.error(f"Alert generation failed: {e}")

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
                "alerts_generated": alerts_generated,
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
        Run AI analysis on markets, grouped by category.
        COMPANION APPROACH: Generate market highlights, not betting recommendations.
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

        # Group patterns by category (for additional context)
        promising_patterns = [p for p in patterns if p.confidence_score and p.confidence_score > 50]
        for pattern in promising_patterns:
            market = next((m for m in markets if m.market_id == pattern.market_id), None)
            title = market.title if market else ""
            category = self._infer_category(title)

            if category not in pattern_by_category:
                pattern_by_category[category] = []

            pattern_by_category[category].append({
                "market_id": pattern.market_id,
                "pattern_type": pattern.pattern_type.value,
                "description": pattern.description,
            })

        # Fetch news context for each category via Gemini web search
        logger.info("Fetching real news context via Gemini web search...")
        category_news: Dict[str, Dict[str, Any]] = {}

        for category, category_markets in market_by_category.items():
            if len(category_markets) >= 3:
                try:
                    titles = [m["title"] for m in category_markets[:10]]
                    logger.info(f"Fetching news for {category} ({len(titles)} market titles)...")
                    category_news[category] = await search_category_news(category, titles)

                    # Log results
                    news = category_news[category]
                    if news.get("error"):
                        logger.warning(f"Gemini search error for {category}: {news['error']}")
                    else:
                        logger.info(f"Got {len(news.get('headlines', []))} headlines for {category}")

                except Exception as e:
                    logger.error(f"Failed to fetch news for {category}: {e}")
                    category_news[category] = {"error": str(e), "headlines": []}

        # Analyze each category separately (with real news context!)
        categories_analyzed = 0
        for category, category_markets in market_by_category.items():
            if not category_markets:
                continue

            # Analyze any category with at least 3 markets
            if len(category_markets) < 3:
                continue

            try:
                logger.info(f"Analyzing category '{category}': {len(category_markets)} markets")

                # Pass news context from Gemini to Groq
                news_context = category_news.get(category, {})

                result = await ai_agent.analyze_category_batch(
                    category=category,
                    markets=category_markets,
                    patterns=pattern_by_category.get(category, []),
                    news_context=news_context  # NEW: Real news from Gemini
                )

                # COMPANION: Save highlights (not opportunities)
                if result and result.get("highlights"):
                    for highlight in result["highlights"]:
                        await self.save_market_highlight(
                            highlight, category, session, news_context
                        )
                        saved += 1

                categories_analyzed += 1
                logger.info(f"Category '{category}' analysis: {len(result.get('highlights', []))} highlights found")

            except Exception as e:
                logger.error(f"Category analysis failed for {category}: {e}")

        # Run cross-platform price gap analysis (informational, not arbitrage hunting)
        try:
            kalshi_markets = [m for m in markets if m.platform == "kalshi"]
            poly_markets = [m for m in markets if m.platform == "polymarket"]

            if kalshi_markets and poly_markets:
                kalshi_dicts = [{"market_id": m.market_id, "title": m.title, "yes_price": m.yes_price, "volume": m.volume} for m in kalshi_markets[:30]]
                poly_dicts = [{"market_id": m.market_id, "title": m.title, "yes_price": m.yes_price, "volume": m.volume} for m in poly_markets[:30]]

                arb_result = await ai_agent.analyze_cross_platform_arbitrage(kalshi_dicts, poly_dicts)
                if arb_result:
                    arb_saved = await self.save_arbitrage_opportunities(arb_result, session)
                    logger.info(f"Saved {arb_saved} price gap findings")

        except Exception as e:
            logger.error(f"Price gap analysis failed: {e}")

        await session.commit()
        logger.info(f"AI analysis complete: {saved} insights saved across {categories_analyzed} categories")
        return saved

    def _calculate_interest_score(
        self,
        highlight: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate how interesting/important this insight is.
        Used for ranking insights on the frontend.
        """
        score = 50  # Base

        # Volume boost
        volume = market_data.get("volume", 0) if market_data else highlight.get("volume", 0)
        if volume:
            if volume > 1_000_000:
                score += 20
            elif volume > 100_000:
                score += 10
            elif volume > 10_000:
                score += 5

        # Movement boost - bigger moves are more interesting
        movement = highlight.get("recent_movement", "")
        if movement:
            try:
                # Parse "+5%" or "-3%" etc
                pct_str = movement.replace("%", "").replace("+", "").replace("-", "").split()[0]
                pct = float(pct_str)
                if pct > 10:
                    score += 15
                elif pct > 5:
                    score += 10
                elif pct > 2:
                    score += 5
            except (ValueError, IndexError):
                pass

        # Catalyst boost - markets with upcoming events are more interesting
        if highlight.get("upcoming_catalyst"):
            score += 10

        # Analyst note boost - if AI had good insight
        analyst_note = highlight.get("analyst_note", "")
        if analyst_note and len(analyst_note) > 100:
            score += 5

        # Cap at 100
        return min(100, score)

    async def save_market_highlight(
        self,
        highlight: Dict[str, Any],
        category: str,
        session: AsyncSession,
        news_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save a market highlight to the database.
        COMPANION APPROACH: We inform and contextualize, not recommend bets.

        Args:
            highlight: AI-generated highlight data
            category: Market category
            session: Database session
            news_context: Gemini search results (THE HOMEWORK)
        """
        try:
            # Extract current odds from various possible formats
            current_odds = highlight.get("current_odds", {})
            if not current_odds and highlight.get("yes_price"):
                current_odds = {
                    "yes": highlight.get("yes_price"),
                    "no": highlight.get("no_price")
                }

            # Extract source articles from news context (THE HOMEWORK)
            source_articles = []
            if news_context and news_context.get("headlines"):
                for h in news_context["headlines"][:5]:
                    source_articles.append({
                        "title": h.get("title", ""),
                        "source": h.get("source", ""),
                        "date": h.get("date", ""),
                        "relevance": h.get("relevance", ""),
                    })

            # Calculate dynamic interest score
            interest_score = self._calculate_interest_score(highlight)

            insight = AIInsight(
                market_id=highlight.get("market_id", "unknown"),
                market_title=highlight.get("market_title", ""),
                platform=highlight.get("platform", "unknown"),
                category=category,

                # Market summary (COMPANION STYLE)
                summary=highlight.get("summary", "Market analysis pending"),
                current_odds=current_odds,
                implied_probability=highlight.get("implied_probability", ""),

                # Activity & movement
                volume_note=highlight.get("volume_note", ""),
                recent_movement=highlight.get("recent_movement", ""),
                movement_context=highlight.get("movement_context", ""),

                # Upcoming events
                upcoming_catalyst=highlight.get("upcoming_catalyst", ""),

                # Analyst context
                analyst_note=highlight.get("analyst_note", ""),

                # Source articles (THE HOMEWORK - from Gemini web search)
                source_articles=source_articles if source_articles else None,
                news_context=news_context if news_context else None,

                # Dynamic interest score for ranking
                interest_score=interest_score,

                expires_at=datetime.utcnow() + timedelta(hours=24),
                status="active"
            )
            session.add(insight)
            logger.debug(f"Saved highlight for {highlight.get('market_id')} ({category}) - interest={interest_score}")
        except Exception as e:
            logger.error(f"Failed to save market highlight: {e}")

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
        """
        Generate daily digest using AI agent.
        COMPANION APPROACH: News briefing, not betting tips.
        """
        if not ai_agent.is_enabled():
            return None

        async with AsyncSessionLocal() as session:
            # Get recent market highlights
            result = await session.execute(
                select(AIInsight)
                .where(AIInsight.status == "active")
                .where(AIInsight.created_at > datetime.utcnow() - timedelta(hours=24))
                .order_by(AIInsight.interest_score.desc().nullslast())
                .limit(50)
            )
            insights = result.scalars().all()

            if not insights:
                logger.info("No recent insights for digest")
                return None

            # Convert to dicts for AI (COMPANION STYLE)
            market_highlights = []
            for i in insights:
                market_highlights.append({
                    "market_id": i.market_id,
                    "market_title": i.market_title,
                    "platform": i.platform,
                    "category": i.category,
                    "summary": i.summary,
                    "current_odds": i.current_odds,
                    "implied_probability": i.implied_probability,
                    "volume_note": i.volume_note,
                    "recent_movement": i.recent_movement,
                    "upcoming_catalyst": i.upcoming_catalyst,
                    "analyst_note": i.analyst_note,
                })

            # Generate digest with AI (COMPANION STYLE - news briefing)
            digest = await ai_agent.generate_daily_digest(market_highlights)

            if digest:
                # Save digest with COMPANION fields
                daily = DailyDigest(
                    digest_date=datetime.utcnow().date(),
                    tier=tier,
                    headline=digest.get("headline", ""),
                    top_movers=digest.get("top_movers", []),
                    most_active=digest.get("most_active", []),
                    upcoming_catalysts=digest.get("upcoming_catalysts", []),
                    category_snapshots=digest.get("category_snapshots", {}),
                    notable_price_gaps=digest.get("notable_price_gaps", []),
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
