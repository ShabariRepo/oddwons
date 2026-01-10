"""
Background Worker Service for OddWons.

This runs as a separate process/container from the API server.
Handles all long-running tasks:
- Data collection from Kalshi/Polymarket
- AI analysis (Groq/Gemini)
- Cross-platform market matching
- Alert generation

For local dev: docker-compose up worker
For Railway: Separate worker service with cron trigger
"""
import asyncio
import logging
import os
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_data_collection():
    """Collect market data from Kalshi and Polymarket."""
    logger.info("Starting data collection...")
    try:
        from app.services.data_collector import data_collector
        result = await data_collector.run_collection()
        logger.info(f"Data collection complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        raise


async def run_analysis():
    """Run pattern detection and AI analysis."""
    logger.info("Starting analysis...")
    try:
        from app.services.patterns.engine import pattern_engine
        result = await pattern_engine.run_full_analysis()
        logger.info(f"Analysis complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


async def run_market_matching():
    """Run cross-platform market matching."""
    logger.info("Starting market matching...")
    try:
        from app.services.market_matcher import run_market_matching
        result = await run_market_matching(min_volume=1000)
        logger.info(f"Market matching complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Market matching failed: {e}")
        raise


async def run_full_pipeline():
    """Run the complete data pipeline: collect -> analyze -> match."""
    start = datetime.utcnow()
    logger.info("=" * 50)
    logger.info(f"Starting full pipeline at {start.isoformat()}")
    logger.info("=" * 50)

    try:
        # Step 1: Data collection
        await run_data_collection()

        # Step 2: Analysis (patterns + AI insights)
        await run_analysis()

        # Step 3: Cross-platform matching
        await run_market_matching()

        elapsed = (datetime.utcnow() - start).total_seconds()
        logger.info(f"Full pipeline complete in {elapsed:.1f}s")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler."""
    scheduler = AsyncIOScheduler()

    # Get interval from env (default 15 minutes)
    interval_minutes = int(os.getenv("WORKER_INTERVAL_MINUTES", "15"))

    # Add the main pipeline job
    scheduler.add_job(
        run_full_pipeline,
        IntervalTrigger(minutes=interval_minutes),
        id="full_pipeline",
        name="Full Data Pipeline",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    # Daily digest generation (8 AM UTC)
    # scheduler.add_job(
    #     generate_daily_digest,
    #     CronTrigger(hour=8, minute=0),
    #     id="daily_digest",
    #     name="Daily Digest Generation",
    # )

    logger.info(f"Scheduler configured with {interval_minutes} minute interval")
    return scheduler


async def main():
    """Main entry point for the worker."""
    logger.info("OddWons Worker starting...")

    # Check if we should run once (for Railway cron) or continuously
    run_once = os.getenv("WORKER_RUN_ONCE", "false").lower() == "true"

    if run_once:
        # Railway cron mode: run once and exit
        logger.info("Running in single-execution mode (WORKER_RUN_ONCE=true)")
        await run_full_pipeline()
        logger.info("Single execution complete, exiting.")
    else:
        # Continuous mode: run scheduler
        logger.info("Running in continuous scheduler mode")

        # Run immediately on startup
        run_on_start = os.getenv("WORKER_RUN_ON_START", "true").lower() == "true"
        if run_on_start:
            logger.info("Running initial pipeline on startup...")
            try:
                await run_full_pipeline()
            except Exception as e:
                logger.error(f"Initial pipeline failed: {e}")

        # Start scheduler for subsequent runs
        scheduler = create_scheduler()
        scheduler.start()

        logger.info("Worker scheduler started. Press Ctrl+C to exit.")

        # Keep running
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down worker...")
            scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
