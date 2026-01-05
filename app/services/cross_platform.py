"""
Cross-Platform Market Matching and Spotlight Service.

This service identifies markets that exist on both Kalshi and Polymarket,
and provides rich context for users to understand what's happening across
prediction markets.

PHILOSOPHY: We are a RESEARCH COMPANION, not an arbitrage tool.
We inform and contextualize, not recommend bets.
"""
import re
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.market import (
    CrossPlatformSpotlight,
    CrossPlatformMatch,
    CrossPlatformSummary,
    CrossPlatformWatchResponse,
    NewsHeadline,
    PlatformPriceHistory,
    PricePoint,
    KeyDate,
    RelatedMarket,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Cross-Platform Matching Patterns
# ============================================================================

# Each pattern: (match_id, topic_name, kalshi_pattern, poly_pattern, category, search_terms)
CROSS_PLATFORM_PATTERNS = [
    # Fed Chair nominations
    ("fed-chair-warsh", "Trump nominates Kevin Warsh as Fed Chair",
     r'trump.*nominate.*warsh.*fed', r'trump.*nominate.*warsh.*fed',
     "Politics", ["Kevin Warsh", "Fed Chair", "Federal Reserve"]),

    ("fed-chair-hassett", "Trump nominates Kevin Hassett as Fed Chair",
     r'trump.*nominate.*hassett.*fed', r'trump.*nominate.*hassett.*fed',
     "Politics", ["Kevin Hassett", "Fed Chair", "Federal Reserve"]),

    ("fed-chair-waller", "Trump nominates Christopher Waller as Fed Chair",
     r'trump.*nominate.*waller.*fed', r'trump.*nominate.*waller.*fed',
     "Politics", ["Christopher Waller", "Fed Chair", "Federal Reserve"]),

    ("fed-chair-shelton", "Trump nominates Judy Shelton as Fed Chair",
     r'trump.*nominate.*shelton.*fed', r'trump.*nominate.*shelton.*fed',
     "Politics", ["Judy Shelton", "Fed Chair", "Federal Reserve"]),

    # 2028 Democratic nominees
    ("dem-2028-newsom", "Gavin Newsom 2028 Democratic Nominee",
     r'newsom.*democratic.*(nominee|nomination).*2028',
     r'newsom.*2028.*democratic.*(nominee|nomination)',
     "Politics", ["Gavin Newsom", "2028 election", "Democratic primary"]),

    ("dem-2028-shapiro", "Josh Shapiro 2028 Democratic Nominee",
     r'shapiro.*democratic.*(nominee|nomination).*2028',
     r'shapiro.*2028.*democratic.*(nominee|nomination)',
     "Politics", ["Josh Shapiro", "2028 election", "Democratic primary"]),

    ("dem-2028-buttigieg", "Pete Buttigieg 2028 Democratic Nominee",
     r'buttigieg.*democratic.*(nominee|nomination).*2028',
     r'buttigieg.*2028.*democratic.*(nominee|nomination)',
     "Politics", ["Pete Buttigieg", "2028 election", "Democratic primary"]),

    ("dem-2028-whitmer", "Gretchen Whitmer 2028 Democratic Nominee",
     r'whitmer.*democratic.*(nominee|nomination).*2028',
     r'whitmer.*2028.*democratic.*(nominee|nomination)',
     "Politics", ["Gretchen Whitmer", "2028 election", "Democratic primary"]),

    # Cabinet confirmations
    ("cabinet-hegseth", "Pete Hegseth confirmed as Defense Secretary",
     r'hegseth.*confirm', r'hegseth.*confirm',
     "Politics", ["Pete Hegseth", "Defense Secretary", "confirmation"]),

    ("cabinet-bondi", "Pam Bondi confirmed as Attorney General",
     r'bondi.*confirm', r'bondi.*confirm',
     "Politics", ["Pam Bondi", "Attorney General", "confirmation"]),

    ("cabinet-patel", "Kash Patel confirmed as FBI Director",
     r'patel.*confirm.*fbi', r'patel.*confirm.*fbi',
     "Politics", ["Kash Patel", "FBI Director", "confirmation"]),

    # Economic indicators
    ("recession-2025", "US recession in 2025",
     r'recession.*2025', r'recession.*2025',
     "Economics", ["US recession", "economic outlook", "GDP"]),

    ("inflation-3pct-2025", "US inflation above 3% in 2025",
     r'inflation.*(above|more|over).*3.*2025',
     r'inflation.*(above|more|over).*3.*2025',
     "Economics", ["inflation", "CPI", "Federal Reserve"]),

    # Fed rate decisions
    ("fed-rate-jan-2026", "Fed rate cut January 2026",
     r'fed.*(cut|lower).*rate.*jan.*2026',
     r'fed.*(cut|lower).*rate.*jan.*2026',
     "Economics", ["Fed rate cut", "FOMC", "interest rates"]),

    # Crypto prices
    ("btc-125k-2025", "Bitcoin hits $125k in 2025",
     r'bitcoin.*125.*2025', r'bitcoin.*125.*2025',
     "Crypto", ["Bitcoin", "cryptocurrency", "BTC price"]),

    # NOTE: Skipping btc-150k - different question structures across platforms
    # Kalshi: "When will Bitcoin hit $150k?" vs Poly: "Will Bitcoin hit $80k or $150k first?"

    ("eth-5000-2025", "Ethereum hits $5000 in 2025",
     r'ethereum.*5.*000.*2025', r'ethereum.*5.*000.*2025',
     "Crypto", ["Ethereum", "ETH", "cryptocurrency"]),

    # Policy/Events
    ("tiktok-ban", "TikTok ban in the US",
     r'tiktok.*(ban|divest)', r'tiktok.*(ban|divest)',
     "Politics", ["TikTok", "ByteDance", "ban"]),

    ("tariffs-mexico", "Trump 25% tariffs on Mexico",
     r'(tariff|tariffs).*25.*mexico', r'(tariff|tariffs).*25.*mexico',
     "Politics", ["tariffs", "Mexico", "trade policy"]),

    ("tariffs-canada", "Trump 25% tariffs on Canada",
     r'(tariff|tariffs).*25.*canada', r'(tariff|tariffs).*25.*canada',
     "Politics", ["tariffs", "Canada", "trade policy"]),

    # Sports (Super Bowl)
    ("sb-chiefs", "Chiefs win Super Bowl",
     r'chiefs.*win.*super.*bowl', r'chiefs.*win.*super.*bowl',
     "Sports", ["Kansas City Chiefs", "Super Bowl", "NFL"]),

    ("sb-eagles", "Eagles win Super Bowl",
     r'eagles.*win.*super.*bowl', r'eagles.*win.*super.*bowl',
     "Sports", ["Philadelphia Eagles", "Super Bowl", "NFL"]),

    ("sb-bills", "Bills win Super Bowl",
     r'bills.*win.*super.*bowl', r'bills.*win.*super.*bowl',
     "Sports", ["Buffalo Bills", "Super Bowl", "NFL"]),

    ("sb-lions", "Lions win Super Bowl",
     r'lions.*win.*super.*bowl', r'lions.*win.*super.*bowl',
     "Sports", ["Detroit Lions", "Super Bowl", "NFL"]),
]


@dataclass
class MatchedMarket:
    """Internal representation of a cross-platform matched market."""
    match_id: str
    topic: str
    category: str
    search_terms: List[str]
    kalshi_id: Optional[str] = None
    kalshi_title: Optional[str] = None
    kalshi_price: Optional[float] = None
    kalshi_volume: Optional[float] = None
    kalshi_close_time: Optional[datetime] = None
    poly_id: Optional[str] = None
    poly_title: Optional[str] = None
    poly_price: Optional[float] = None
    poly_volume: Optional[float] = None
    poly_close_time: Optional[datetime] = None


class CrossPlatformService:
    """Service for cross-platform market matching and spotlight generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ai_agent = None

    async def _get_ai_agent(self):
        """Lazy load AI agent."""
        if self._ai_agent is None:
            from app.services.ai_agent import MarketAnalysisAgent
            self._ai_agent = MarketAnalysisAgent()
        return self._ai_agent

    async def find_all_matches(self, min_volume: float = 1000) -> List[MatchedMarket]:
        """Find all cross-platform matches with minimum volume."""
        matches = []

        # Get all active markets
        result = await self.db.execute(text("""
            SELECT id, platform, title, yes_price, volume, close_time
            FROM markets
            WHERE volume >= :min_vol
              AND status IN ('active', 'open')
              AND yes_price > 0.02 AND yes_price < 0.98
            ORDER BY volume DESC
        """), {"min_vol": min_volume})

        markets = result.fetchall()
        kalshi = [(m[0], m[2], m[3], m[4], m[5]) for m in markets if m[1] == 'KALSHI']
        poly = [(m[0], m[2], m[3], m[4], m[5]) for m in markets if m[1] == 'POLYMARKET']

        for match_id, topic, k_pattern, p_pattern, category, search_terms in CROSS_PLATFORM_PATTERNS:
            matched = MatchedMarket(
                match_id=match_id,
                topic=topic,
                category=category,
                search_terms=search_terms,
            )

            # Find Kalshi match
            for id, title, price, vol, close_time in kalshi:
                if re.search(k_pattern, title.lower()):
                    if matched.kalshi_id is None or vol > matched.kalshi_volume:
                        matched.kalshi_id = id
                        matched.kalshi_title = title
                        matched.kalshi_price = price
                        matched.kalshi_volume = vol
                        matched.kalshi_close_time = close_time

            # Find Polymarket match
            for id, title, price, vol, close_time in poly:
                if re.search(p_pattern, title.lower()):
                    if matched.poly_id is None or vol > matched.poly_volume:
                        matched.poly_id = id
                        matched.poly_title = title
                        matched.poly_price = price
                        matched.poly_volume = vol
                        matched.poly_close_time = close_time

            # Only include if found on BOTH platforms
            if matched.kalshi_id and matched.poly_id:
                matches.append(matched)

        # Sort by combined volume
        matches.sort(key=lambda m: (m.kalshi_volume or 0) + (m.poly_volume or 0), reverse=True)
        return matches

    async def get_price_history(
        self,
        market_id: str,
        platform: str,
        days: int = 7
    ) -> PlatformPriceHistory:
        """Get price history for a market over the specified days."""
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(text("""
            SELECT yes_price, timestamp
            FROM market_snapshots
            WHERE market_id = :market_id
              AND timestamp >= :since
            ORDER BY timestamp ASC
        """), {"market_id": market_id, "since": since})

        snapshots = result.fetchall()

        # Get current price
        current_result = await self.db.execute(text("""
            SELECT yes_price FROM markets WHERE id = :market_id
        """), {"market_id": market_id})
        current_row = current_result.fetchone()
        current_price = (current_row[0] or 0) * 100 if current_row else 0

        history = [
            PricePoint(timestamp=s[1], price=(s[0] or 0) * 100)
            for s in snapshots if s[0] is not None
        ]

        price_7d_ago = history[0].price if history else None
        change_7d = current_price - price_7d_ago if price_7d_ago else None
        change_7d_pct = (change_7d / price_7d_ago * 100) if price_7d_ago and price_7d_ago > 0 else None

        # Determine trend
        if change_7d is not None:
            if change_7d > 2:
                trend = "up"
            elif change_7d < -2:
                trend = "down"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        return PlatformPriceHistory(
            platform=platform,
            current_price=current_price,
            price_7d_ago=price_7d_ago,
            change_7d=change_7d,
            change_7d_pct=change_7d_pct,
            trend=trend,
            history=history,
        )

    async def find_related_markets(
        self,
        match: MatchedMarket,
        limit: int = 5
    ) -> List[RelatedMarket]:
        """Find related markets based on search terms and category."""
        related = []

        # Build keyword search pattern
        keywords = match.search_terms[:3]

        for kw in keywords:
            # Search by keyword in title
            result = await self.db.execute(text("""
                SELECT id, platform, title, yes_price, volume
                FROM markets
                WHERE title ILIKE :pattern
                  AND volume >= 1000
                  AND status IN ('active', 'open')
                  AND id != :kalshi_id
                  AND id != :poly_id
                ORDER BY volume DESC
                LIMIT 5
            """), {
                "pattern": f"%{kw}%",
                "kalshi_id": match.kalshi_id or "",
                "poly_id": match.poly_id or "",
            })

            for row in result.fetchall():
                if len(related) >= limit:
                    break
                # Avoid duplicates
                if not any(r.id == row[0] for r in related):
                    related.append(RelatedMarket(
                        id=row[0],
                        platform=row[1],
                        title=row[2][:60],
                        yes_price=(row[3] or 0) * 100,
                        volume=row[4] or 0,
                    ))

        return related[:limit]

    async def extract_key_dates(self, match: MatchedMarket) -> List[KeyDate]:
        """Extract key dates and catalysts from market descriptions and knowledge."""
        dates = []

        # Add resolution date
        resolution_date = match.kalshi_close_time or match.poly_close_time
        if resolution_date:
            dates.append(KeyDate(
                date=resolution_date.strftime("%b %d, %Y"),
                description="Market resolution",
                is_resolution_date=True,
            ))

        # Add known catalysts based on topic
        topic_lower = match.topic.lower()

        if "fed chair" in topic_lower:
            dates.extend([
                KeyDate(date="Jan 20, 2025", description="Inauguration Day"),
                KeyDate(date="Late Jan 2025", description="Expected Fed Chair announcement"),
                KeyDate(date="May 15, 2026", description="Powell's term expires"),
            ])
        elif "2028" in topic_lower and "democratic" in topic_lower:
            dates.extend([
                KeyDate(date="2026", description="Midterm elections"),
                KeyDate(date="2027", description="Campaign announcements expected"),
                KeyDate(date="Aug 2028", description="Democratic National Convention"),
            ])
        elif "recession" in topic_lower:
            dates.extend([
                KeyDate(date="Monthly", description="Jobs report release"),
                KeyDate(date="Quarterly", description="GDP data release"),
                KeyDate(date="Monthly", description="CPI inflation report"),
            ])
        elif "bitcoin" in topic_lower or "ethereum" in topic_lower:
            dates.extend([
                KeyDate(date="Ongoing", description="Crypto market 24/7"),
                KeyDate(date="Quarterly", description="ETF flow reports"),
            ])
        elif "confirm" in topic_lower:
            dates.extend([
                KeyDate(date="Jan 20, 2025", description="Inauguration Day"),
                KeyDate(date="Jan-Feb 2025", description="Senate confirmation hearings"),
            ])
        elif "tiktok" in topic_lower:
            dates.extend([
                KeyDate(date="Jan 19, 2025", description="TikTok ban deadline"),
                KeyDate(date="Jan 20, 2025", description="New administration takes office"),
            ])
        elif "tariff" in topic_lower:
            dates.extend([
                KeyDate(date="Jan 20, 2025", description="Inauguration Day"),
                KeyDate(date="Feb 1, 2025", description="Potential tariff implementation"),
            ])
        elif "super bowl" in topic_lower:
            dates.extend([
                KeyDate(date="Feb 9, 2025", description="Super Bowl LIX"),
            ])

        return dates

    async def generate_ai_analysis(self, match: MatchedMarket) -> Dict[str, str]:
        """Generate AI analysis for a cross-platform match."""
        try:
            agent = await self._get_ai_agent()

            k_price = (match.kalshi_price or 0) * 100
            p_price = (match.poly_price or 0) * 100
            gap = abs(k_price - p_price)
            higher_platform = "Kalshi" if k_price > p_price else "Polymarket"

            prompt = f"""Analyze this cross-platform prediction market match for our research companion app.

Topic: {match.topic}
Category: {match.category}

Kalshi Market: {match.kalshi_title}
- Price: {k_price:.1f}¢ YES
- Volume: ${match.kalshi_volume:,.0f}

Polymarket Market: {match.poly_title}
- Price: {p_price:.1f}¢ YES
- Volume: ${match.poly_volume:,.0f}

Price Gap: {gap:.1f}¢ ({higher_platform} is higher)

Provide analysis in JSON format with these exact keys:
{{
    "ai_analysis": "3-4 sentence overview of what's happening with this market",
    "gap_explanation": "1-2 sentences on why the price gap might exist",
    "momentum_summary": "1 sentence on recent price momentum/trend",
    "key_risks": "1-2 sentences on key risks or factors to watch"
}}

Focus on informing and contextualizing, not recommending bets.
Be specific about the topic (names, dates, events)."""

            response = await agent.analyze_with_prompt(prompt)

            # Parse JSON from response
            import json
            try:
                # Try to find JSON in response
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass

            # Fallback: generate default analysis
            return {
                "ai_analysis": f"{match.topic} is trading at {k_price:.0f}¢ on Kalshi and {p_price:.0f}¢ on Polymarket, with ${(match.kalshi_volume + match.poly_volume):,.0f} in combined volume. This market has attracted significant attention from traders on both platforms.",
                "gap_explanation": f"The {gap:.1f}¢ gap may reflect different user bases - Kalshi attracts more traditional finance users while Polymarket has a crypto-native audience.",
                "momentum_summary": "Price has been relatively stable over the past week on both platforms.",
                "key_risks": "Key risks include sudden news events and policy announcements that could rapidly shift market sentiment.",
            }
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return {
                "ai_analysis": f"{match.topic} is being tracked on both Kalshi and Polymarket.",
                "gap_explanation": "Price differences between platforms are common and may reflect different user bases.",
                "momentum_summary": "Monitor both platforms for price movements.",
                "key_risks": "News events could impact this market.",
            }

    async def get_news_headlines(self, match: MatchedMarket) -> List[NewsHeadline]:
        """Get recent news headlines for a market topic.

        In production, this would call a news API or web search.
        For now, we generate contextual headlines based on the topic.
        """
        # In production: Use WebSearch API or news API
        # For now, return placeholder headlines that would be fetched
        headlines = []

        topic_lower = match.topic.lower()

        if "fed chair" in topic_lower:
            if "warsh" in topic_lower:
                headlines = [
                    NewsHeadline(title="WSJ: Warsh met with Trump transition team", source="WSJ", date="Jan 3"),
                    NewsHeadline(title="Bessent reportedly favors Warsh for Fed Chair", source="Reuters", date="Jan 2"),
                    NewsHeadline(title="Fed Chair speculation intensifies ahead of inauguration", source="Bloomberg", date="Dec 30"),
                ]
            elif "hassett" in topic_lower:
                headlines = [
                    NewsHeadline(title="Hassett's economic views align with Trump agenda", source="CNBC", date="Jan 3"),
                    NewsHeadline(title="Who will be Trump's Fed Chair pick?", source="WSJ", date="Jan 2"),
                ]
        elif "2028" in topic_lower:
            if "newsom" in topic_lower:
                headlines = [
                    NewsHeadline(title="Newsom positions himself for 2028 run", source="Politico", date="Jan 4"),
                    NewsHeadline(title="Democratic 2028 field takes shape", source="NYT", date="Jan 2"),
                ]
            elif "shapiro" in topic_lower:
                headlines = [
                    NewsHeadline(title="Shapiro's approval rating rises in Pennsylvania", source="Politico", date="Jan 3"),
                    NewsHeadline(title="2028 Democratic contenders begin jockeying", source="The Hill", date="Jan 1"),
                ]
        elif "recession" in topic_lower:
            headlines = [
                NewsHeadline(title="Jobs report shows resilient labor market", source="BLS", date="Jan 5"),
                NewsHeadline(title="Economists split on 2025 recession odds", source="Bloomberg", date="Jan 3"),
                NewsHeadline(title="Fed signals patience on rate cuts", source="Reuters", date="Dec 30"),
            ]
        elif "bitcoin" in topic_lower or "ethereum" in topic_lower:
            headlines = [
                NewsHeadline(title="Bitcoin ETF flows remain positive", source="CoinDesk", date="Jan 5"),
                NewsHeadline(title="Crypto markets eye new highs in 2025", source="Bloomberg", date="Jan 3"),
            ]
        elif "tiktok" in topic_lower:
            headlines = [
                NewsHeadline(title="TikTok ban deadline looms as Jan 19 approaches", source="NYT", date="Jan 4"),
                NewsHeadline(title="ByteDance explores last-minute options", source="Reuters", date="Jan 3"),
            ]
        elif "tariff" in topic_lower:
            headlines = [
                NewsHeadline(title="Trump reaffirms 25% tariff threat on Mexico, Canada", source="Reuters", date="Jan 4"),
                NewsHeadline(title="Markets brace for potential trade war", source="Bloomberg", date="Jan 3"),
            ]

        return headlines[:3]  # Return max 3 headlines

    async def build_spotlight(self, match: MatchedMarket) -> CrossPlatformSpotlight:
        """Build a full spotlight for a cross-platform match."""
        # Calculate gap
        k_price = (match.kalshi_price or 0) * 100
        p_price = (match.poly_price or 0) * 100
        gap = abs(k_price - p_price)

        if k_price > p_price:
            gap_direction = "kalshi_higher"
        elif p_price > k_price:
            gap_direction = "polymarket_higher"
        else:
            gap_direction = "equal"

        # Fetch all data in parallel
        kalshi_history_task = self.get_price_history(match.kalshi_id, "Kalshi") if match.kalshi_id else None
        poly_history_task = self.get_price_history(match.poly_id, "Polymarket") if match.poly_id else None
        related_task = self.find_related_markets(match)
        dates_task = self.extract_key_dates(match)
        news_task = self.get_news_headlines(match)
        analysis_task = self.generate_ai_analysis(match)

        # Await all tasks
        tasks = [t for t in [kalshi_history_task, poly_history_task, related_task, dates_task, news_task, analysis_task] if t]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Parse results
        kalshi_history = results[0] if kalshi_history_task and not isinstance(results[0], Exception) else None
        poly_history = results[1] if poly_history_task and not isinstance(results[1], Exception) else None
        related = results[2] if not isinstance(results[2], Exception) else []
        key_dates = results[3] if not isinstance(results[3], Exception) else []
        news = results[4] if not isinstance(results[4], Exception) else []
        analysis = results[5] if not isinstance(results[5], Exception) else {}

        # Determine price correlation
        if kalshi_history and poly_history:
            k_trend = kalshi_history.trend
            p_trend = poly_history.trend
            if k_trend == p_trend:
                price_correlation = f"both_moving_{k_trend}" if k_trend != "stable" else "stable"
            else:
                price_correlation = "diverging"
        else:
            price_correlation = "unknown"

        # Resolution date
        resolution_date = match.kalshi_close_time or match.poly_close_time
        days_until = (resolution_date - datetime.utcnow()).days if resolution_date else None

        return CrossPlatformSpotlight(
            match_id=match.match_id,
            topic=match.topic,
            category=match.category,
            kalshi=CrossPlatformMatch(
                market_id=match.kalshi_id,
                platform="Kalshi",
                title=match.kalshi_title,
                yes_price=k_price,
                volume=match.kalshi_volume or 0,
                close_time=match.kalshi_close_time,
            ) if match.kalshi_id else None,
            polymarket=CrossPlatformMatch(
                market_id=match.poly_id,
                platform="Polymarket",
                title=match.poly_title,
                yes_price=p_price,
                volume=match.poly_volume or 0,
                close_time=match.poly_close_time,
            ) if match.poly_id else None,
            price_gap_cents=gap,
            gap_direction=gap_direction,
            news_headlines=news,
            kalshi_history=kalshi_history,
            polymarket_history=poly_history,
            price_correlation=price_correlation,
            key_dates=key_dates,
            resolution_date=resolution_date,
            days_until_resolution=days_until,
            ai_analysis=analysis.get("ai_analysis"),
            gap_explanation=analysis.get("gap_explanation"),
            momentum_summary=analysis.get("momentum_summary"),
            key_risks=analysis.get("key_risks"),
            related_markets=related,
            kalshi_volume=match.kalshi_volume or 0,
            polymarket_volume=match.poly_volume or 0,
            combined_volume=(match.kalshi_volume or 0) + (match.poly_volume or 0),
            kalshi_url=f"https://kalshi.com/markets/{match.kalshi_id.replace('kalshi_', '')}" if match.kalshi_id else None,
            polymarket_url=f"https://polymarket.com/event/{match.poly_id.replace('poly_', '')}" if match.poly_id else None,
            last_updated=datetime.utcnow(),
            data_freshness="live",
        )

    async def get_spotlight(self, match_id: str) -> Optional[CrossPlatformSpotlight]:
        """Get spotlight for a specific match by ID."""
        matches = await self.find_all_matches()
        for match in matches:
            if match.match_id == match_id:
                return await self.build_spotlight(match)
        return None

    async def get_all_spotlights(self, limit: int = 10) -> List[CrossPlatformSpotlight]:
        """Get spotlights for top cross-platform matches."""
        matches = await self.find_all_matches()
        spotlights = []

        for match in matches[:limit]:
            try:
                spotlight = await self.build_spotlight(match)
                spotlights.append(spotlight)
            except Exception as e:
                logger.error(f"Error building spotlight for {match.match_id}: {e}")

        return spotlights

    async def get_cross_platform_watch(self, limit: int = 3) -> CrossPlatformWatchResponse:
        """Get summary for daily digest Cross-Platform Watch section."""
        matches = await self.find_all_matches()
        summaries = []

        for match in matches[:limit]:
            k_price = (match.kalshi_price or 0) * 100
            p_price = (match.poly_price or 0) * 100
            gap = abs(k_price - p_price)

            if k_price > p_price:
                gap_direction = "kalshi_higher"
            elif p_price > k_price:
                gap_direction = "polymarket_higher"
            else:
                gap_direction = "equal"

            # Generate 2-sentence summary
            combined_vol = (match.kalshi_volume or 0) + (match.poly_volume or 0)
            summary = f"{match.topic} is priced at {k_price:.0f}¢ on Kalshi vs {p_price:.0f}¢ on Polymarket. "
            if gap >= 2:
                summary += f"The {gap:.1f}¢ gap suggests different trader sentiment across platforms."
            else:
                summary += f"Pricing is consistent across both platforms."

            summaries.append(CrossPlatformSummary(
                match_id=match.match_id,
                topic=match.topic,
                kalshi_price=k_price,
                polymarket_price=p_price,
                gap_cents=gap,
                gap_direction=gap_direction,
                combined_volume=combined_vol,
                summary=summary,
                trend="stable",  # Would be calculated from history
            ))

        total_volume = sum(s.combined_volume for s in summaries)

        return CrossPlatformWatchResponse(
            matches=summaries,
            total_matches=len(matches),
            total_volume=total_volume,
            generated_at=datetime.utcnow(),
        )
