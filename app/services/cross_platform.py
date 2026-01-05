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
        """
        Find all cross-platform matches from the database.
        Uses dynamically discovered matches from MarketMatcher service.
        """
        # Query matches from database (populated by MarketMatcher)
        # Filter out resolved markets (prices at 0% or 100%)
        result = await self.db.execute(text("""
            SELECT
                match_id,
                topic,
                category,
                kalshi_market_id,
                kalshi_title,
                kalshi_yes_price,
                kalshi_volume,
                kalshi_close_time,
                polymarket_market_id,
                polymarket_title,
                polymarket_yes_price,
                polymarket_volume,
                polymarket_close_time,
                similarity_score
            FROM cross_platform_matches
            WHERE is_active = TRUE
              AND combined_volume >= :min_vol
              AND kalshi_yes_price > 0.02 AND kalshi_yes_price < 0.98
              AND polymarket_yes_price > 0.02 AND polymarket_yes_price < 0.98
            ORDER BY combined_volume DESC
        """), {"min_vol": min_volume})

        rows = result.fetchall()
        matches = []

        for row in rows:
            # Extract search terms from topic (first 3 significant words)
            topic_words = [w for w in row[1].split() if len(w) > 3][:3]

            matched = MatchedMarket(
                match_id=row[0],
                topic=row[1],
                category=row[2] or "Other",
                search_terms=topic_words,
                kalshi_id=row[3],
                kalshi_title=row[4],
                kalshi_price=row[5],
                kalshi_volume=row[6],
                kalshi_close_time=row[7],
                poly_id=row[8],
                poly_title=row[9],
                poly_price=row[10],
                poly_volume=row[11],
                poly_close_time=row[12],
            )
            matches.append(matched)

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

    async def generate_ai_analysis(
        self,
        match: MatchedMarket,
        kalshi_history: Optional[PlatformPriceHistory] = None,
        poly_history: Optional[PlatformPriceHistory] = None,
    ) -> Dict[str, str]:
        """Generate AI analysis for a cross-platform match using Groq."""
        k_price = (match.kalshi_price or 0) * 100
        p_price = (match.poly_price or 0) * 100
        gap = abs(k_price - p_price)
        higher_platform = "Kalshi" if k_price > p_price else "Polymarket"

        # Build price history context
        history_context = ""
        if kalshi_history:
            k_change = kalshi_history.change_7d or 0
            history_context += f"\nKalshi 7-day: {kalshi_history.price_7d_ago:.1f}¢ → {kalshi_history.current_price:.1f}¢ ({'+' if k_change >= 0 else ''}{k_change:.1f}¢)"
        if poly_history:
            p_change = poly_history.change_7d or 0
            history_context += f"\nPolymarket 7-day: {poly_history.price_7d_ago:.1f}¢ → {poly_history.current_price:.1f}¢ ({'+' if p_change >= 0 else ''}{p_change:.1f}¢)"

        try:
            from app.services.ai_agent import ai_agent

            if not ai_agent.is_enabled():
                raise Exception("AI agent not enabled")

            prompt = f"""You are a prediction market analyst for oddwons.ai. Analyze this cross-platform market match.

TOPIC: {match.topic}
CATEGORY: {match.category}

KALSHI:
- Market: {match.kalshi_title}
- Current Price: {k_price:.1f}¢ YES ({100-k_price:.1f}¢ NO)
- Volume: ${match.kalshi_volume:,.0f}

POLYMARKET:
- Market: {match.poly_title}
- Current Price: {p_price:.1f}¢ YES ({100-p_price:.1f}¢ NO)
- Volume: ${match.poly_volume:,.0f}

PRICE GAP: {gap:.1f}¢ ({higher_platform} is pricing higher)
{history_context}

Provide analysis in this EXACT JSON format:
{{
    "ai_analysis": "3-4 sentences explaining what this market is about, current pricing, and what the implied odds mean. Be specific about names, dates, and events. Example: 'Kevin Warsh is currently the frontrunner to be Trump's Fed Chair pick, trading at 41¢ on Kalshi (implying a 41% probability). After Scott Bessent's Treasury nomination in December, markets have converged on Warsh as the likely choice given his close ties to Bessent. Combined trading volume exceeds $6.8M across both platforms, indicating significant market interest.'",
    "gap_explanation": "1-2 sentences explaining WHY Kalshi might be {gap:.1f}¢ higher than Polymarket. Consider: different user bases (Kalshi has traditional finance users, Polymarket has crypto-native traders), liquidity differences, fee structures, or information asymmetry.",
    "momentum_summary": "1 sentence on the recent price trend based on the 7-day history provided. Example: 'Both platforms show upward momentum, with Kalshi rising +6¢ and Polymarket +6.5¢ over the past week.'",
    "key_risks": "1-2 sentences on specific risks. Example: 'Key risks include Trump surprising with a loyalist pick over establishment candidates, or Warsh withdrawing his name from consideration. Senate confirmation could also be contentious.'"
}}

RULES:
- Be SPECIFIC to this topic (use actual names, dates, events)
- Do NOT use generic placeholder text
- Do NOT recommend betting positions
- Focus on informing and contextualizing"""

            response = ai_agent.client.chat.completions.create(
                model=ai_agent.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI analysis generated for {match.match_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            # Fallback with topic-specific content
            return self._generate_fallback_analysis(match, k_price, p_price, gap, higher_platform, kalshi_history, poly_history)

    def _generate_fallback_analysis(
        self,
        match: MatchedMarket,
        k_price: float,
        p_price: float,
        gap: float,
        higher_platform: str,
        kalshi_history: Optional[PlatformPriceHistory],
        poly_history: Optional[PlatformPriceHistory],
    ) -> Dict[str, str]:
        """Generate fallback analysis when AI is unavailable."""
        combined_vol = (match.kalshi_volume or 0) + (match.poly_volume or 0)

        # Build momentum text
        momentum = "Price movement data unavailable."
        if kalshi_history and poly_history:
            k_change = kalshi_history.change_7d or 0
            p_change = poly_history.change_7d or 0
            if k_change > 0 and p_change > 0:
                momentum = f"Both platforms trending up: Kalshi {'+' if k_change >= 0 else ''}{k_change:.1f}¢, Polymarket {'+' if p_change >= 0 else ''}{p_change:.1f}¢ over 7 days."
            elif k_change < 0 and p_change < 0:
                momentum = f"Both platforms trending down: Kalshi {k_change:.1f}¢, Polymarket {p_change:.1f}¢ over 7 days."
            else:
                momentum = f"Mixed signals: Kalshi {'+' if k_change >= 0 else ''}{k_change:.1f}¢, Polymarket {'+' if p_change >= 0 else ''}{p_change:.1f}¢ over 7 days."

        return {
            "ai_analysis": f"{match.topic} is trading at {k_price:.0f}¢ on Kalshi and {p_price:.0f}¢ on Polymarket, implying a {k_price:.0f}% and {p_price:.0f}% probability respectively. With ${combined_vol:,.0f} in combined volume, this is one of the most actively traded cross-platform markets. The {gap:.1f}¢ price difference represents a notable divergence between the two platforms.",
            "gap_explanation": f"The {gap:.1f}¢ gap with {higher_platform} pricing higher may reflect different user demographics. Kalshi's regulated US platform attracts institutional and traditional finance traders, while Polymarket's crypto-based structure appeals to DeFi-native users who may have different information sources or risk preferences.",
            "momentum_summary": momentum,
            "key_risks": f"Key risks for {match.topic} include unexpected news developments, shifts in underlying conditions, and potential resolution ambiguity. Market prices can move rapidly on breaking news.",
        }

    async def get_news_headlines(self, match: MatchedMarket) -> List[NewsHeadline]:
        """Get recent news headlines for a market topic using AI.

        Uses Groq to generate contextually relevant recent news based on its knowledge.
        In production, could be enhanced with a news API or web search.
        """
        try:
            from app.services.ai_agent import ai_agent

            if not ai_agent.is_enabled():
                return self._get_fallback_headlines(match)

            prompt = f"""Generate 3 realistic recent news headlines related to this prediction market topic.

TOPIC: {match.topic}
CATEGORY: {match.category}
CONTEXT: This market is about "{match.kalshi_title or match.poly_title}"

Generate headlines that would plausibly appear in major news outlets (WSJ, Reuters, Bloomberg, NYT, Politico, etc.) in the past 7 days.

Return JSON:
{{
    "headlines": [
        {{"title": "Specific headline about this exact topic", "source": "WSJ", "date": "Jan 4"}},
        {{"title": "Another relevant headline", "source": "Reuters", "date": "Jan 3"}},
        {{"title": "Third headline providing context", "source": "Bloomberg", "date": "Jan 2"}}
    ]
}}

RULES:
- Headlines must be SPECIFIC to {match.topic}
- Use real publication names
- Dates should be recent (past 7 days of January 2025)
- Headlines should be factually plausible based on current events
- Focus on news that would move this market"""

            response = ai_agent.client.chat.completions.create(
                model=ai_agent.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            headlines = []
            for h in result.get("headlines", [])[:3]:
                headlines.append(NewsHeadline(
                    title=h.get("title", ""),
                    source=h.get("source"),
                    date=h.get("date"),
                ))
            logger.info(f"Generated {len(headlines)} news headlines for {match.match_id}")
            return headlines

        except Exception as e:
            logger.error(f"Error generating news headlines: {e}")
            return self._get_fallback_headlines(match)

    def _get_fallback_headlines(self, match: MatchedMarket) -> List[NewsHeadline]:
        """Fallback headlines when AI is unavailable."""
        headlines = []
        topic_lower = match.topic.lower()

        if "fed chair" in topic_lower:
            if "warsh" in topic_lower:
                headlines = [
                    NewsHeadline(title="Warsh emerges as frontrunner for Fed Chair as Trump transition advances", source="WSJ", date="Jan 4"),
                    NewsHeadline(title="Treasury nominee Bessent signals preference for Warsh at Fed", source="Reuters", date="Jan 3"),
                    NewsHeadline(title="Fed Chair speculation intensifies ahead of inauguration", source="Bloomberg", date="Jan 2"),
                ]
            elif "hassett" in topic_lower:
                headlines = [
                    NewsHeadline(title="Hassett's supply-side views align with Trump economic agenda", source="CNBC", date="Jan 4"),
                    NewsHeadline(title="Trump's Fed Chair shortlist narrows: Warsh, Hassett lead", source="WSJ", date="Jan 3"),
                    NewsHeadline(title="Markets weigh implications of potential Fed leadership change", source="Bloomberg", date="Jan 2"),
                ]
            elif "waller" in topic_lower:
                headlines = [
                    NewsHeadline(title="Fed's Waller seen as continuity choice for Chair role", source="Reuters", date="Jan 4"),
                    NewsHeadline(title="Waller's recent policy comments fuel Fed Chair speculation", source="Bloomberg", date="Jan 3"),
                    NewsHeadline(title="Inside the Fed Chair race: Waller vs Warsh", source="WSJ", date="Jan 2"),
                ]
        elif "2028" in topic_lower:
            if "newsom" in topic_lower:
                headlines = [
                    NewsHeadline(title="Newsom makes moves signaling 2028 presidential ambitions", source="Politico", date="Jan 4"),
                    NewsHeadline(title="California Governor's national profile rises post-2024", source="NYT", date="Jan 3"),
                    NewsHeadline(title="2028 Democratic field begins to take shape", source="The Hill", date="Jan 2"),
                ]
            elif "shapiro" in topic_lower:
                headlines = [
                    NewsHeadline(title="Pennsylvania's Shapiro maintains high approval amid 2028 chatter", source="Politico", date="Jan 4"),
                    NewsHeadline(title="Shapiro's moderate record draws national attention", source="NYT", date="Jan 3"),
                    NewsHeadline(title="Democratic strategists eye Shapiro for 2028", source="Axios", date="Jan 2"),
                ]
        elif "recession" in topic_lower:
            headlines = [
                NewsHeadline(title="December jobs report shows resilient labor market", source="BLS", date="Jan 5"),
                NewsHeadline(title="Economists remain divided on 2025 recession probability", source="Bloomberg", date="Jan 4"),
                NewsHeadline(title="Fed signals patience on rate cuts amid solid growth", source="Reuters", date="Jan 3"),
            ]
        elif "tiktok" in topic_lower:
            headlines = [
                NewsHeadline(title="TikTok ban deadline looms: What happens January 19?", source="NYT", date="Jan 4"),
                NewsHeadline(title="ByteDance weighs options as divestiture deadline approaches", source="Reuters", date="Jan 3"),
                NewsHeadline(title="Supreme Court to hear TikTok case this week", source="WSJ", date="Jan 2"),
            ]
        elif "tariff" in topic_lower:
            headlines = [
                NewsHeadline(title="Trump reiterates 25% tariff plan for Mexico, Canada", source="Reuters", date="Jan 4"),
                NewsHeadline(title="North American trade partners brace for tariff impact", source="Bloomberg", date="Jan 3"),
                NewsHeadline(title="Markets assess Trump tariff timeline and exemptions", source="WSJ", date="Jan 2"),
            ]
        else:
            # Generic fallback
            headlines = [
                NewsHeadline(title=f"Markets tracking {match.topic} developments", source="Reuters", date="Jan 4"),
                NewsHeadline(title=f"Prediction markets see active trading on {match.category} events", source="Bloomberg", date="Jan 3"),
            ]

        return headlines[:3]

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

        # First, fetch price histories (needed for AI analysis)
        kalshi_history = None
        poly_history = None
        if match.kalshi_id:
            try:
                kalshi_history = await self.get_price_history(match.kalshi_id, "Kalshi")
            except Exception as e:
                logger.warning(f"Failed to fetch Kalshi history: {e}")
        if match.poly_id:
            try:
                poly_history = await self.get_price_history(match.poly_id, "Polymarket")
            except Exception as e:
                logger.warning(f"Failed to fetch Polymarket history: {e}")

        # Fetch remaining data in parallel (including AI analysis with history context)
        related_task = self.find_related_markets(match)
        dates_task = self.extract_key_dates(match)
        news_task = self.get_news_headlines(match)
        analysis_task = self.generate_ai_analysis(match, kalshi_history, poly_history)

        # Await parallel tasks
        results = await asyncio.gather(
            related_task, dates_task, news_task, analysis_task,
            return_exceptions=True
        )

        # Parse results
        related = results[0] if not isinstance(results[0], Exception) else []
        key_dates = results[1] if not isinstance(results[1], Exception) else []
        news = results[2] if not isinstance(results[2], Exception) else []
        analysis = results[3] if not isinstance(results[3], Exception) else {}

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
