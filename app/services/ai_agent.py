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


# Category-specific prompt templates with domain knowledge
CATEGORY_PROMPTS = {
    "politics": {
        "context": """You are an expert political analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Polling aggregates vs individual polls (RCP, 538, Polymarket consensus)
- Electoral college math - not just popular vote
- Swing state dynamics (PA, MI, WI, AZ, GA, NV, NC)
- Incumbency advantage (~3-5 points historically)
- Primary vs general election dynamics
- Debate effects typically fade within 1-2 weeks
- October surprise patterns - late breaks often go to challenger
- Early voting and mail-in ballot patterns
- Senate/House correlation with presidential races
- Gubernatorial races as bellwethers

EDGE OPPORTUNITIES TO LOOK FOR:
- Markets not reflecting recent polling shifts
- Correlated races mispriced (if X wins, Y likely wins)
- Time decay on event-specific markets (debate, speech, endorsement)
- State-level vs national polling divergence
- Primary momentum not priced into general election markets""",
        "focus": "polling trends, electoral math, state-by-state correlations, timing relative to key events"
    },

    "sports": {
        "context": """You are an expert sports betting analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Injury reports and their actual impact (star players vs role players)
- Rest days and back-to-back game fatigue
- Home court/field advantage varies by sport (NBA ~3pts, NFL ~2.5pts, MLB minimal)
- Momentum and winning/losing streaks - often overvalued
- Playoff experience and pressure situations
- Weather impact (outdoor sports, especially NFL, golf)
- Travel and timezone effects (West Coast teams traveling East)
- Referee/umpire tendencies for totals
- Line movement and sharp money indicators
- Divisional/rivalry game intensity
- Late-season motivation (tank mode, playoff positioning)

EDGE OPPORTUNITIES TO LOOK FOR:
- Public overreaction to recent results (recency bias)
- Star player returns not fully priced in
- Weather changes after line is set
- Back-to-back situations undervalued
- Playoff seeding implications not reflected
- Prop markets with informational lag vs main lines""",
        "focus": "injury impact, situational factors, public vs sharp money, line movement, rest advantages"
    },

    "crypto": {
        "context": """You are an expert crypto analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Bitcoin dominance and altcoin correlation (BTC moves, alts follow 2-3x)
- On-chain metrics: exchange inflows/outflows, whale wallets, miner behavior
- Macro correlation: BTC increasingly correlated with risk assets (NASDAQ, SPY)
- Halving cycles and supply dynamics
- ETF flows (spot Bitcoin ETFs, futures ETFs)
- Regulatory calendar: SEC deadlines, CFTC rulings, Congressional hearings
- Stablecoin flows (USDT/USDC minting = dry powder entering)
- Funding rates on perpetuals (positive = overleveraged longs)
- Fear & Greed index extremes often mark local tops/bottoms
- DeFi TVL trends and protocol-specific catalysts
- Airdrop and unlock schedules (token supply events)

EDGE OPPORTUNITIES TO LOOK FOR:
- Price targets set before major regulatory news
- Correlation breakdown opportunities (BTC vs specific alts)
- Token unlocks not priced into short-term markets
- ETF decision dates with binary outcomes
- Stablecoin reserves signaling institutional interest
- On-chain data diverging from price action""",
        "focus": "on-chain signals, regulatory catalysts, correlation patterns, supply events, institutional flows"
    },

    "finance": {
        "context": """You are an expert financial markets analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Fed meeting calendar and dot plot projections
- Inflation data (CPI, PCE, PPI) release schedule and expectations
- Employment data (NFP, unemployment, jobless claims)
- Earnings season timing and sector rotation
- Treasury yield curve dynamics (2y-10y spread)
- VIX levels and volatility regime
- Dollar strength (DXY) impact on multinational earnings
- Sector correlations (tech vs rates, energy vs oil)
- Year-end window dressing and tax-loss selling
- Options expiration (OPEX) effects on index levels
- Buyback blackout periods

EDGE OPPORTUNITIES TO LOOK FOR:
- Fed funds futures vs market pricing disconnect
- Earnings expectations vs actual guidance trends
- Macro data surprises (actual vs consensus)
- Sector rotation signals not reflected in index bets
- Rate cut/hike probabilities mispriced vs Fed rhetoric
- Seasonal patterns (Santa rally, January effect, sell in May)""",
        "focus": "Fed policy expectations, earnings catalysts, macro data releases, rate sensitivity, seasonal patterns"
    },

    "entertainment": {
        "context": """You are an expert entertainment industry analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Awards season calendar (Guild awards → Critics Choice → Globes → Oscars)
- Guild awards (SAG, DGA, WGA, PGA) are strong Oscar predictors
- Box office opening weekend vs legs (multiplier patterns)
- Streaming vs theatrical release dynamics
- Critic scores (Rotten Tomatoes, Metacritic) impact on awards
- Category fraud (lead vs supporting placement)
- Campaign spending and "For Your Consideration" timing
- International markets and foreign language categories
- Documentary and short film specialized predictors
- TV ratings and streaming viewership metrics
- Celebrity news cycle impact on projects

EDGE OPPORTUNITIES TO LOOK FOR:
- Guild award results not fully priced into Oscar markets
- Late-breaking scandals affecting campaigns
- International film momentum (Festival circuit → Oscars)
- Box office overperformance signaling broader appeal
- Category placement changes affecting odds
- Preferential ballot dynamics for Best Picture""",
        "focus": "precursor awards, campaign momentum, guild voting patterns, category dynamics, critical reception"
    },

    "tech": {
        "context": """You are an expert technology analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Product launch calendars (Apple events, Google I/O, CES)
- Antitrust and regulatory proceedings timeline
- AI development milestones and benchmarks
- Chip supply and semiconductor cycle
- Big Tech earnings as market bellwethers
- Startup funding rounds and valuation trends
- Patent filings and litigation outcomes
- Executive changes and their market impact
- Platform policy changes (App Store, Google Play)
- Cloud infrastructure market share shifts
- M&A regulatory approval timelines

EDGE OPPORTUNITIES TO LOOK FOR:
- Product launch dates with binary outcomes
- Regulatory ruling deadlines
- AI capability milestones (benchmarks, releases)
- Antitrust case rulings with predictable timelines
- Earnings guidance vs whisper numbers
- Executive departure/hiring patterns""",
        "focus": "product launches, regulatory rulings, AI milestones, antitrust outcomes, earnings catalysts"
    },

    "weather": {
        "context": """You are an expert meteorologist specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Model consensus (GFS, Euro, Canadian, NAM)
- European model generally more accurate for medium-range
- Ensemble spread indicates uncertainty
- Tropical storm/hurricane models (NHC cone of uncertainty)
- Seasonal patterns and climate normals
- El Niño/La Niña effects on regional weather
- Record temperature context (daily vs monthly vs all-time)
- Urban heat island effect for city records
- Measurement station locations and biases
- Lead time accuracy degradation (Day 1 vs Day 7)

EDGE OPPORTUNITIES TO LOOK FOR:
- Model divergence creating uncertainty not priced in
- Records that require specific conditions (not just hot/cold)
- Hurricane intensity forecasts typically underestimate rapid intensification
- Seasonal forecasts vs actual pattern evolution
- Climate trend adjustments to historical comparisons""",
        "focus": "model consensus, ensemble uncertainty, historical context, seasonal patterns, measurement specifics"
    },

    "world": {
        "context": """You are an expert geopolitical analyst specializing in prediction markets.

DOMAIN KNOWLEDGE TO APPLY:
- Conflict escalation/de-escalation patterns
- Diplomatic calendar (summits, UN sessions, treaty deadlines)
- Sanctions regimes and enforcement mechanisms
- Military capability assessments
- Economic pressure points and trade dependencies
- Leadership stability and succession dynamics
- Alliance structures (NATO, EU, BRICS, etc.)
- Historical precedents for similar situations
- Intelligence community assessments (when public)
- NGO and think tank analysis
- Local election impacts on foreign policy

EDGE OPPORTUNITIES TO LOOK FOR:
- Summit outcomes with binary possibilities
- Treaty/agreement deadline resolutions
- Sanctions implementation timelines
- Military exercise conclusions
- Leadership health/succession speculation
- Economic data releases from key countries""",
        "focus": "diplomatic timelines, escalation signals, leadership stability, economic pressures, alliance dynamics"
    },

    "other": {
        "context": """You are an expert analyst specializing in prediction markets across various domains.

GENERAL ANALYSIS FRAMEWORK:
- Identify the key drivers of the outcome
- Assess probability vs current market pricing
- Look for informational edges (timing, expertise, data sources)
- Consider liquidity and market efficiency
- Evaluate time decay and event timing
- Check for correlated markets that may be mispriced

EDGE OPPORTUNITIES TO LOOK FOR:
- Information asymmetry (specialized knowledge)
- Timing edges (knowing when resolution data arrives)
- Correlation arbitrage (related outcomes priced inconsistently)
- Liquidity imbalances creating temporary mispricings
- Public sentiment overreaction to recent news""",
        "focus": "information edges, timing, correlation, liquidity dynamics, sentiment analysis"
    }
}


def get_category_prompt(category: str) -> Dict[str, str]:
    """Get category-specific prompt components."""
    return CATEGORY_PROMPTS.get(category.lower(), CATEGORY_PROMPTS["other"])


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
        all_opportunities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate the daily analysis digest for subscribers.
        Ranks opportunities and provides portfolio-level insights.
        """
        if not self.is_enabled():
            return None

        if not all_opportunities:
            return {
                "top_picks": [],
                "avoid_list": [],
                "market_sentiment": "Insufficient data for analysis",
                "arbitrage_opportunities": [],
                "watchlist": [],
                "generated_at": datetime.utcnow().isoformat()
            }

        prompt = f"""You are an expert prediction market analyst creating a daily briefing for paying subscribers.

TODAY'S DETECTED OPPORTUNITIES:
{json.dumps(all_opportunities[:50], indent=2, default=str)}

Create a daily digest in this exact JSON format:
{{
    "top_picks": [
        {{
            "market_id": "id",
            "market_title": "title",
            "recommendation": "STRONG_BET" | "GOOD_BET",
            "one_liner": "Why this is today's top pick",
            "confidence": 0-100
        }}
    ],
    "avoid_list": [
        {{
            "market_id": "id",
            "market_title": "title",
            "reason": "Why to stay away"
        }}
    ],
    "market_sentiment": "Brief overview of overall market conditions",
    "arbitrage_opportunities": [
        {{
            "description": "Cross-platform or related market arb",
            "potential_edge": "X%"
        }}
    ],
    "watchlist": [
        {{
            "market_id": "id",
            "market_title": "title",
            "trigger": "What would make this actionable"
        }}
    ]
}}

Be ruthless. Only include REAL opportunities. Subscribers are paying for alpha, not noise."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
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
        patterns: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Analyze a batch of markets within the same category using specialized prompts.

        Each category gets domain-specific context and expertise:
        - Politics: polling, electoral math, swing states
        - Sports: injuries, rest, home advantage, line movement
        - Crypto: on-chain, regulatory, correlation patterns
        - Finance: Fed, earnings, macro data
        - etc.
        """
        if not self.is_enabled():
            return None

        if not markets:
            return []

        # Get category-specific prompt components
        category_config = get_category_prompt(category)
        category_context = category_config["context"]
        category_focus = category_config["focus"]

        # Limit batch size to keep context manageable
        markets_batch = markets[:15]
        patterns_batch = patterns[:20]

        prompt = f"""{category_context}

=== ANALYSIS TASK ===

Analyze these {category.upper()} markets and identify the BEST betting opportunities.

MARKETS TO ANALYZE:
{json.dumps(markets_batch, indent=2, default=str)}

DETECTED PATTERNS (rule-based signals):
{json.dumps(patterns_batch, indent=2, default=str)}

YOUR ANALYSIS SHOULD FOCUS ON:
{category_focus}

INSTRUCTIONS:
1. Apply your domain knowledge to each market
2. Look for edges the rule-based patterns might miss
3. Identify cross-market correlations within this category
4. Be specific about WHY there's an edge - generic reasoning is worthless
5. Only recommend markets where you see REAL alpha

Return a JSON object:
{{
    "category": "{category}",
    "category_outlook": "1-2 sentence assessment of this category right now",
    "opportunities": [
        {{
            "market_id": "exact market ID from input",
            "market_title": "market title",
            "recommendation": "STRONG_BET" | "GOOD_BET" | "CAUTION" | "AVOID",
            "confidence_score": 0-100,
            "one_liner": "Single actionable sentence a trader can act on",
            "reasoning": "Specific reasoning using domain knowledge - cite specific factors",
            "suggested_position": "YES" | "NO" | "WAIT",
            "edge_explanation": "What specific edge exists (be concrete)",
            "time_sensitivity": "ACT_NOW" | "HOURS" | "DAYS" | "WEEKS",
            "related_markets": ["IDs of correlated markets from this batch"],
            "key_factors": ["Factor 1", "Factor 2"]
        }}
    ],
    "category_insights": [
        "Cross-cutting insight about this category",
        "Pattern noticed across multiple markets"
    ],
    "watch_for": ["Upcoming event/data that could move these markets"]
}}

Quality over quantity. If there's nothing good, say so. Subscribers pay for alpha, not noise."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result["analyzed_at"] = datetime.utcnow().isoformat()
            result["prompt_category"] = category  # Track which prompt was used

            opportunities = result.get("opportunities", [])
            logger.info(f"Category '{category}' analysis: {len(opportunities)} opportunities found")
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
