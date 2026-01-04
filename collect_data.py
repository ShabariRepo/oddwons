#!/usr/bin/env python3
"""
Data Collection Cron Job for Railway.

This script runs on a schedule (every 15 minutes) to collect market data
from Kalshi and Polymarket, then exits cleanly.

Railway cron jobs MUST exit after completion - no long-running processes.

Usage (Railway):
  cronSchedule: "*/15 * * * *"
  startCommand: "python collect_data.py"
"""
import asyncio
import sys
import os
import logging

# Setup logging before imports
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("collect_data")


async def main():
    """Collect market data and exit."""
    try:
        logger.info("Starting data collection...")

        # Import here to avoid issues with missing env vars at module level
        from app.services.data_collector import data_collector

        # Run collection (without pattern detection - that's a separate cron)
        results = await data_collector.run_collection(run_pattern_detection=False)

        logger.info(f"Collection complete: {results}")

        # Report results
        kalshi_count = results.get("kalshi", 0)
        poly_count = results.get("polymarket", 0)
        errors = results.get("errors", [])

        if errors:
            logger.warning(f"Collection completed with errors: {errors}")

        logger.info(f"Collected {kalshi_count} Kalshi markets, {poly_count} Polymarket markets")

        # Exit cleanly - required for Railway cron
        sys.exit(0)

    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        # Non-zero exit triggers restart policy
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
