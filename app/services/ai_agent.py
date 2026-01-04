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

        # Model options by priority:
        # 1. gpt-oss-20b-128k     - 1000 TPS, $0.075 in / $0.30 out  (DEFAULT - fastest, cheapest)
        # 2. qwen3-32b-131k       - 662 TPS,  $0.29 in / $0.59 out   (good balance)
        # 3. llama-4-scout-17bx16e-128k - 594 TPS, $0.11 in / $0.34 out (newer llama)
        # 4. llama-3.3-70b-versatile - 394 TPS, $0.59 in / $0.79 out (slowest, most expensive)
        self.model = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")

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
