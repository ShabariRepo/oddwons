"""
AI-powered market analysis using Groq.
This is the core value prop - NOT rule-based detection.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from groq import Groq

logger = logging.getLogger(__name__)


# =============================================================================
# COMPANION APP APPROACH - We inform and contextualize, NOT recommend bets
# =============================================================================
# oddwons.ai is a research companion for prediction market users.
# Think: Bloomberg Terminal for prediction markets, NOT a tipster.
#
# Users pay for:
# - Curated market summaries
# - Context on price movements
# - Time savings (we do the research)
# - Cross-platform visibility
# - Alerts when markets move
# - Understanding what odds imply
#
# The AI should NEVER return 0 results - there's always something to report.
# =============================================================================

# Category-specific context for analysis (domain knowledge to apply)
CATEGORY_CONTEXT = {
    "politics": """
DOMAIN CONTEXT:
- Polling aggregates (RCP, 538, Polymarket consensus) vs individual polls
- Electoral college math - popular vote ≠ winner
- Key swing states: PA, MI, WI, AZ, GA, NV, NC
- Primary calendar and caucus dates
- Debate schedules and their typical short-term effects
- Approval ratings and historical trends
- Senate/House correlation with presidential races
""",
    "sports": """
DOMAIN CONTEXT:
- Injury report implications (star vs role players)
- Rest days and back-to-back fatigue
- Home court/field advantage by sport
- Playoff seeding implications
- Weather for outdoor events
- Historical head-to-head records
- Line movements from opening
""",
    "crypto": """
DOMAIN CONTEXT:
- ETF flow data and institutional interest
- Halving cycle timing
- Regulatory calendar (SEC deadlines, hearings)
- Major protocol upgrades and forks
- On-chain metrics like exchange reserves
- Correlation with traditional risk assets
- Major conference and announcement dates
""",
    "finance": """
DOMAIN CONTEXT:
- Fed meeting calendar and rate expectations
- CPI/PCE/NFP release dates
- Earnings season timing by sector
- Yield curve status (inverted, steepening)
- VIX levels and volatility regime
- Historical seasonal patterns (January effect, etc.)
""",
    "entertainment": """
DOMAIN CONTEXT:
- Awards season calendar (Guilds → Globes → Oscars)
- Guild awards as Oscar predictors
- Box office performance metrics
- Critical consensus (RT, Metacritic)
- Streaming vs theatrical dynamics
- Festival circuit momentum
""",
    "tech": """
DOMAIN CONTEXT:
- Product launch schedules (Apple events, Google I/O)
- Antitrust proceeding timelines
- AI benchmark releases and milestones
- Earnings dates for major tech
- M&A regulatory approval timelines
""",
    "weather": """
DOMAIN CONTEXT:
- Model consensus (GFS vs Euro)
- Ensemble spread and uncertainty
- Historical climate patterns
- El Niño/La Niña status
- Record-setting context (daily vs all-time)
""",
    "world": """
DOMAIN CONTEXT:
- Diplomatic calendar (summits, UN sessions)
- Sanctions regimes and deadlines
- Alliance structures (NATO, EU, BRICS)
- Leadership stability indicators
- Historical precedents
""",
    "other": """
DOMAIN CONTEXT:
- Key drivers of the outcome
- Timeline to resolution
- Data sources that will determine outcome
- Related markets on same topic
"""
}


def get_category_context(category: str) -> str:
    """Get category-specific context for analysis."""
    return CATEGORY_CONTEXT.get(category.lower(), CATEGORY_CONTEXT["other"])


class MarketAnalysisAgent:
    """
    AI agent for analyzing prediction market opportunities.
    Uses Groq with fast, cheap models for real-time analysis.
    """

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not set - AI analysis disabled")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)

        # Model options by priority (Groq):
        # 1. openai/gpt-oss-20b      - 1000 TPS, $0.075/$0.30, 131k ctx (DEFAULT - fastest, cheapest)
        # 2. openai/gpt-oss-120b     - 500 TPS, $0.15/$0.60, 131k ctx (larger, smarter)
        # 3. llama-3.3-70b-versatile - 280 TPS, $0.59/$0.79, 131k ctx (Meta's best)
        # 4. llama-3.1-8b-instant    - 560 TPS, $0.05/$0.08, 131k ctx (fastest, least smart)
        self.model = os.environ.get("AI_MODEL", "openai/gpt-oss-20b")

    def is_enabled(self) -> bool:
        """Check if AI analysis is enabled."""
        return self.client is not None and os.environ.get("AI_ANALYSIS_ENABLED", "true").lower() == "true"

    async def analyze_opportunity(
        self,
        market_data: Dict[str, Any],
        historical_patterns: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single market opportunity with full context.
        Returns actionable insight with confidence score and reasoning.
        """
        if not self.is_enabled():
            logger.warning("AI analysis disabled - skipping opportunity analysis")
            return None

        prompt = f"""You are an expert prediction market analyst. Analyze this opportunity and provide actionable insights.

MARKET DATA:
{json.dumps(market_data, indent=2, default=str)}

HISTORICAL PATTERNS DETECTED:
{json.dumps(historical_patterns, indent=2, default=str)}

Provide your analysis in this exact JSON format:
{{
    "recommendation": "STRONG_BET" | "GOOD_BET" | "CAUTION" | "AVOID",
    "confidence_score": 0-100,
    "one_liner": "Single sentence a bettor can act on immediately",
    "reasoning": "2-3 sentences explaining WHY this is an opportunity",
    "risk_factors": ["risk1", "risk2"],
    "suggested_position": "YES" | "NO" | "WAIT",
    "edge_explanation": "What edge does the bettor have here that the market is missing?",
    "time_sensitivity": "ACT_NOW" | "HOURS" | "DAYS" | "WEEKS"
}}

Be specific. Be actionable. If there's no real edge, say so. Don't hype garbage opportunities."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result["analyzed_at"] = datetime.utcnow().isoformat()
            result["market_id"] = market_data.get("market_id") or market_data.get("id")
            result["platform"] = market_data.get("platform")

            logger.info(f"AI analysis complete for {result['market_id']}: {result['recommendation']}")
            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None

    async def generate_daily_digest(
        self,
        all_markets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate the daily briefing for subscribers.
        COMPANION APPROACH: Summarize and inform, don't recommend bets.
        """
        if not self.is_enabled():
            return None

        if not all_markets:
            return {
                "headline": "No market data available for today's digest",
                "top_movers": [],
                "most_active": [],
                "upcoming_catalysts": [],
                "category_snapshots": {},
                "notable_price_gaps": [],
                "generated_at": datetime.utcnow().isoformat()
            }

        prompt = f"""You are creating a daily briefing for oddwons.ai subscribers who want to stay informed about prediction markets.

TODAY'S MARKET DATA:
{json.dumps(all_markets[:50], indent=2, default=str)}

Create a daily digest that a busy professional can scan in 2 minutes:

{{
    "headline": "One sentence summary of today's prediction market landscape",

    "top_movers": [
        {{
            "market_title": "...",
            "platform": "kalshi|polymarket",
            "movement": "+12% today",
            "current_price": 0.65,
            "context": "Brief explanation of why it moved"
        }}
    ],

    "most_active": [
        {{
            "market_title": "...",
            "platform": "...",
            "volume_note": "High volume today",
            "current_odds": {{"yes": 0.72, "no": 0.28}},
            "what_it_means": "Brief explanation"
        }}
    ],

    "upcoming_catalysts": [
        {{
            "event": "Fed Rate Decision",
            "date": "Jan 15",
            "affected_categories": ["finance", "crypto"],
            "what_to_watch": "Brief explanation"
        }}
    ],

    "category_snapshots": {{
        "politics": "1-2 sentence summary of political markets",
        "sports": "1-2 sentence summary",
        "crypto": "1-2 sentence summary",
        "finance": "1-2 sentence summary"
    }},

    "notable_price_gaps": [
        {{
            "topic": "Same event on both platforms",
            "kalshi_price": 0.55,
            "polymarket_price": 0.62,
            "note": "7 cent difference between platforms"
        }}
    ]
}}

GUIDELINES:
- This is a NEWS BRIEFING, not betting advice
- Focus on WHAT'S HAPPENING, not what to bet on
- Explain movements, don't exploit them
- Help users understand the market landscape
- Be concise and scannable
- DO NOT use words like "BET", "EDGE", "ALPHA", "RECOMMENDATION"
- DO NOT suggest positions or confidence scores"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result["generated_at"] = datetime.utcnow().isoformat()

            logger.info(f"Daily digest generated: {len(result.get('top_picks', []))} top picks")
            return result

        except Exception as e:
            logger.error(f"Daily digest generation failed: {e}")
            return None

    async def analyze_category_batch(
        self,
        category: str,
        markets: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        news_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a batch of markets within the same category.

        COMPANION APPROACH: We summarize and contextualize, NOT recommend bets.
        This should ALWAYS return highlights - there's always something to report.

        Args:
            category: Market category (politics, sports, crypto, etc.)
            markets: List of market data dicts
            patterns: List of detected patterns
            news_context: Real news context from Gemini web search (optional)
        """
        if not self.is_enabled():
            return None

        if not markets:
            return {"category": category, "highlights": [], "category_summary": "No markets in this category."}

        # Get category-specific context
        domain_context = get_category_context(category)

        # Limit batch size to keep context manageable
        max_markets = 10 if len(markets) > 50 else 15
        markets_batch = markets[:max_markets]

        # Build news section from Gemini search results
        news_section = ""
        if news_context and not news_context.get("error"):
            headlines = news_context.get("headlines", [])[:5]
            if headlines:
                news_section = "\nRECENT NEWS (from web search):\n" + "\n".join(
                    f"- {h.get('title', '')} ({h.get('source', '')}, {h.get('date', '')})"
                    for h in headlines
                )

            if news_context.get("category_summary"):
                news_section += f"\n\nCATEGORY CONTEXT: {news_context['category_summary']}"

            key_events = news_context.get("key_events", [])[:3]
            if key_events:
                news_section += "\n\nKEY EVENTS:\n" + "\n".join(
                    f"- {e.get('event', '')} ({e.get('date', '')}): {e.get('impact', '')}"
                    for e in key_events
                )

        prompt = f"""You are a prediction market analyst for oddwons.ai - but you're also a chill bro who makes finance fun and accessible.

YOUR VIBE: Think smart friend who's really into prediction markets and explains things in a casual, engaging way. You're informative AND entertaining. Use casual language naturally - "yo", "lowkey", "no cap", "let's go", "wild", "spicy", "heating up", "locked in" etc. Keep it fun but still helpful.

{domain_context}
{news_section}

MARKETS TO ANALYZE ({category.upper()}):
{json.dumps(markets_batch, indent=2, default=str)}

For each interesting market, provide analysis that incorporates the recent news above.
Focus on WHY prices are where they are based on actual events.

TONE EXAMPLES:
- Instead of: "Market shows elevated probability due to recent polling"
- Say: "Yo this market is heating up - recent polls got it jumping to 62%, no cap"

- Instead of: "Significant price movement following news event"
- Say: "Bro this thing moved HARD after the news dropped - we're talking +12% in like 2 hours"

- Instead of: "Catalyst approaching that may impact pricing"
- Say: "Big date coming up fam - the Fed meeting on the 15th could make this spicy"

- Instead of: "Low liquidity may result in price volatility"
- Say: "Heads up - this one's kinda thin so prices can swing wild"

Return your analysis as JSON:
{{
    "category": "{category}",
    "market_count": {len(markets_batch)},
    "highlights": [
        {{
            "market_id": "exact ID from input",
            "market_title": "title",
            "platform": "kalshi or polymarket",
            "summary": "Brief explanation with bro vibes - what's this market about?",
            "current_odds": {{"yes": 0.62, "no": 0.38}},
            "implied_probability": "62% chance - that's like saying...",
            "volume_note": "This one's getting action" | "Pretty chill volume" | "Kinda dead tbh",
            "recent_movement": "+5% this week, let's go" | "Chillin, no big moves" | "Down 3%, oof",
            "movement_context": "Why it moved - connect to actual news above",
            "upcoming_catalyst": "Mark your calendar fam - Jan 15th" | "Nothing major on deck",
            "analyst_note": "One sentence takeaway with personality"
        }}
    ],
    "category_summary": "2-3 sentence overview with bro energy - what's poppin in this category",
    "upcoming_events": ["List of upcoming events - keep it real"]
}}

CRITICAL GUIDELINES:
- ALWAYS return 3-5+ highlights (there's always something worth noting)
- DO NOT use words like "BET", "EDGE", "ALPHA", "STRONG_BET" - we inform, not recommend
- DO NOT recommend positions (YES/NO) or give betting advice
- DO explain what the odds MEAN with helpful context and personality
- DO connect price movements to the ACTUAL NEWS provided above
- DO mention upcoming events that could move markets
- BE THE SMART FRIEND who makes prediction markets fun and accessible
- Keep it real, keep it chill, but keep it INFORMATIVE"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result["analyzed_at"] = datetime.utcnow().isoformat()
            result["category"] = category

            highlights = result.get("highlights", [])
            logger.info(f"Category '{category}' analysis: {len(highlights)} highlights generated")
            return result

        except Exception as e:
            logger.error(f"Category batch analysis failed for {category}: {e}")
            return None

    async def analyze_cross_platform_arbitrage(
        self,
        kalshi_markets: List[Dict[str, Any]],
        polymarket_markets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find arbitrage opportunities between Kalshi and Polymarket.
        """
        if not self.is_enabled():
            return None

        if not kalshi_markets and not polymarket_markets:
            return {"arbitrage_opportunities": [], "analyzed_at": datetime.utcnow().isoformat()}

        # Limit data size for API call
        kalshi_sample = kalshi_markets[:30] if kalshi_markets else []
        poly_sample = polymarket_markets[:30] if polymarket_markets else []

        prompt = f"""You are an arbitrage specialist analyzing prediction markets across platforms.

KALSHI MARKETS:
{json.dumps(kalshi_sample, indent=2, default=str)}

POLYMARKET MARKETS:
{json.dumps(poly_sample, indent=2, default=str)}

Find ANY of these opportunities:
1. Same event priced differently across platforms
2. Related events where combined probabilities don't make sense
3. Temporal arbitrage (same event, different time horizons)
4. Hedging opportunities

Return JSON:
{{
    "arbitrage_opportunities": [
        {{
            "type": "CROSS_PLATFORM" | "RELATED_MARKET" | "TEMPORAL" | "HEDGE",
            "description": "Clear description",
            "kalshi_market": "market details",
            "polymarket_market": "market details",
            "edge_percentage": "estimated edge",
            "execution_steps": ["step1", "step2"],
            "risks": ["risk1"],
            "confidence": 0-100
        }}
    ]
}}

Only include opportunities with >2% edge. Be specific about execution."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result["analyzed_at"] = datetime.utcnow().isoformat()

            opps = result.get("arbitrage_opportunities", [])
            logger.info(f"Arbitrage analysis complete: {len(opps)} opportunities found")
            return result

        except Exception as e:
            logger.error(f"Arbitrage analysis failed: {e}")
            return None


# Singleton instance
ai_agent = MarketAnalysisAgent()
