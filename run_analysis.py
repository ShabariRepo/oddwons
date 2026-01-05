#!/usr/bin/env python3
"""
AI Analysis Cron Job for Railway.

This script runs on a schedule (offset from data collection) to:
1. Run rule-based pattern detection on recent data
2. Run AI analysis on promising patterns
3. Find cross-platform arbitrage opportunities
4. Store actionable insights

Railway cron jobs MUST exit after completion - no long-running processes.

Usage (Railway):
  cronSchedule: "5,20,35,50 * * * *"  (5 minutes after each data collection)
  startCommand: "python run_analysis.py"
"""
import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging before imports
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run_analysis")


async def main():
    """Run pattern detection, AI analysis, and cross-platform matching, then exit."""
    try:
        logger.info("Starting analysis run...")

        # Check if AI is enabled
        ai_enabled = os.environ.get("AI_ANALYSIS_ENABLED", "true").lower() == "true"
        groq_key = os.environ.get("GROQ_API_KEY")

        if ai_enabled and not groq_key:
            logger.warning("AI_ANALYSIS_ENABLED=true but GROQ_API_KEY not set. Running without AI.")
            ai_enabled = False

        # Import here to avoid issues with missing env vars at module level
        from app.services.patterns.engine import pattern_engine
        from app.services.market_matcher import run_market_matching

        # Run full analysis (pattern detection + AI analysis)
        results = await pattern_engine.run_full_analysis(with_ai=ai_enabled)

        logger.info(f"Analysis complete: {results}")

        # Report results
        patterns = results.get("total_patterns_detected", 0)
        ai_insights = results.get("ai_insights_saved", 0)
        markets = results.get("total_markets_analyzed", 0)

        logger.info(
            f"Analyzed {markets} markets, "
            f"detected {patterns} patterns, "
            f"generated {ai_insights} AI insights"
        )

        # Run cross-platform market matching
        logger.info("Running cross-platform market matching...")
        match_results = await run_market_matching(min_volume=1000)
        matches_found = match_results.get("matches_found", 0)
        new_matches = match_results.get("new_matches", 0)
        updated_matches = match_results.get("updated_matches", 0)

        logger.info(
            f"Cross-platform matching: {matches_found} matches found "
            f"({new_matches} new, {updated_matches} updated)"
        )

        # Exit cleanly - required for Railway cron
        sys.exit(0)

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        # Non-zero exit triggers restart policy
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
