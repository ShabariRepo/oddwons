"""
Background Worker Service for OddWons.

This runs as a separate process/container from the API server.
Handles all long-running tasks:
- Data collection from Kalshi/Polymarket
- AI analysis (Groq/Gemini)
- Cross-platform market matching
- Alert generation
- Email notifications (trial reminders, daily digest, alert emails)

For local dev: docker-compose up worker
For Railway: Separate worker service with cron trigger
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta

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


async def send_trial_reminders():
    """Send trial ending reminder emails (1 day before expiry)."""
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.user import User, SubscriptionStatus
    from app.services.notifications import notification_service

    logger.info("Checking for trial reminders to send...")

    async with AsyncSessionLocal() as session:
        try:
            tomorrow = datetime.utcnow() + timedelta(days=1)
            today = datetime.utcnow()

            result = await session.execute(
                select(User).where(
                    and_(
                        User.subscription_status == SubscriptionStatus.TRIALING,
                        User.trial_end.isnot(None),
                        User.trial_end > today,
                        User.trial_end <= tomorrow,
                        User.trial_reminder_sent == False,
                        User.email_alerts_enabled == True
                    )
                )
            )
            users = result.scalars().all()

            sent_count = 0
            for user in users:
                try:
                    tier = user.subscription_tier.value if user.subscription_tier else "BASIC"
                    await notification_service.send_trial_ending_email(
                        to_email=user.email,
                        user_name=user.name,
                        days_remaining=1,
                        tier=tier
                    )
                    user.trial_reminder_sent = True
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send trial reminder to {user.email}: {e}")

            await session.commit()
            logger.info(f"Sent {sent_count} trial reminder emails")

        except Exception as e:
            logger.error(f"Error in send_trial_reminders: {e}")


async def send_daily_digest_emails():
    """Send daily digest emails to subscribers with digest enabled."""
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.user import User, SubscriptionStatus, SubscriptionTier
    from app.models.ai_insight import AIInsight
    from app.services.notifications import notification_service

    logger.info("Sending daily digest emails...")

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(
                    and_(
                        User.subscription_status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
                        User.subscription_tier.in_([SubscriptionTier.BASIC, SubscriptionTier.PREMIUM, SubscriptionTier.PRO]),
                        User.email_digest_enabled == True
                    )
                )
            )
            users = result.scalars().all()

            if not users:
                logger.info("No users eligible for daily digest")
                return

            yesterday = datetime.utcnow() - timedelta(hours=24)
            insights_result = await session.execute(
                select(AIInsight)
                .where(AIInsight.created_at >= yesterday)
                .order_by(AIInsight.interest_score.desc())
                .limit(5)
            )
            insights = insights_result.scalars().all()

            if not insights:
                logger.info("No insights to include in daily digest")
                return

            opportunities = []
            for insight in insights:
                opportunities.append({
                    "title": insight.market_title or "Market Insight",
                    "description": insight.summary or "",
                    "score": insight.interest_score or 50
                })

            sent_count = 0
            for user in users:
                try:
                    await notification_service.send_daily_digest(
                        to_email=user.email,
                        opportunities=opportunities,
                        user_name=user.name
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send digest to {user.email}: {e}")

            logger.info(f"Sent {sent_count} daily digest emails")

        except Exception as e:
            logger.error(f"Error in send_daily_digest_emails: {e}")


async def process_alert_emails():
    """Process pending alert emails in batches."""
    from sqlalchemy import select, and_
    from app.core.database import AsyncSessionLocal
    from app.models.market import Alert
    from app.models.user import User
    from app.services.notifications import notification_service

    logger.info("Processing pending alert emails...")

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.email_sent == False,
                        Alert.user_id.isnot(None)
                    )
                ).limit(50)
            )
            alerts = result.scalars().all()

            if not alerts:
                logger.info("No pending alert emails")
                return

            sent_count = 0
            for alert in alerts:
                user_result = await session.execute(
                    select(User).where(User.id == alert.user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user or not user.email_alerts_enabled:
                    alert.email_sent = True
                    continue

                try:
                    await notification_service.send_alert_email(
                        to_email=user.email,
                        alert={
                            "title": alert.title,
                            "message": alert.message,
                            "action_suggestion": alert.action_suggestion,
                            "pattern_type": alert.min_tier,
                            "score": 70
                        },
                        user_name=user.name
                    )
                    alert.email_sent = True
                    alert.email_sent_at = datetime.utcnow()
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send alert email: {e}")

            await session.commit()
            logger.info(f"Sent {sent_count} alert emails")

        except Exception as e:
            logger.error(f"Error in process_alert_emails: {e}")


async def run_full_pipeline():
    """Run the complete data pipeline: collect -> analyze -> match -> emails."""
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

        # Step 4: Process pending alert emails
        await process_alert_emails()

        elapsed = (datetime.utcnow() - start).total_seconds()
        logger.info(f"Full pipeline complete in {elapsed:.1f}s")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


async def run_daily_jobs():
    """Run daily scheduled jobs (digest + trial reminders)."""
    logger.info("Running daily email jobs...")
    try:
        await send_trial_reminders()
        await send_daily_digest_emails()
        logger.info("Daily email jobs complete")
    except Exception as e:
        logger.error(f"Daily jobs failed: {e}")


async def post_to_x(post_type: str = "morning"):
    """Post to X (Twitter) account."""
    logger.info(f"Running X post job: {post_type}")
    try:
        from app.services.x_poster import run_scheduled_posts
        result = await run_scheduled_posts(post_type)
        logger.info(f"X post complete: {result}")
        return result
    except Exception as e:
        logger.error(f"X post failed: {e}")
        return None


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler."""
    scheduler = AsyncIOScheduler()

    # Get interval from env (default 15 minutes)
    interval_minutes = int(os.getenv("WORKER_INTERVAL_MINUTES", "15"))

    # Main pipeline job (data collection + AI analysis + market matching)
    scheduler.add_job(
        run_full_pipeline,
        IntervalTrigger(minutes=interval_minutes),
        id="full_pipeline",
        name="Full Data Pipeline",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    # Daily digest emails - 8:00 AM UTC
    scheduler.add_job(
        send_daily_digest_emails,
        CronTrigger(hour=8, minute=0),
        id="daily_digest",
        name="Daily Digest Emails",
        replace_existing=True,
    )

    # Trial reminder emails - 10:00 AM UTC
    scheduler.add_job(
        send_trial_reminders,
        CronTrigger(hour=10, minute=0),
        id="trial_reminders",
        name="Trial Reminder Emails",
        replace_existing=True,
    )

    # Alert emails - every 5 minutes (in addition to running after each pipeline)
    scheduler.add_job(
        process_alert_emails,
        IntervalTrigger(minutes=5),
        id="alert_emails",
        name="Process Alert Emails",
        replace_existing=True,
    )

    # =========================================================================
    # X (TWITTER) POSTING JOBS - HOURLY from 8 AM - 10 PM EST + Late Night
    # EST = UTC - 5
    # ~19 posts/day = ~570/month (under 1,500 limit)
    # =========================================================================

    # --- MORNING BLOCK (8 AM - 12 PM EST) ---
    # 8 AM EST (13:00 UTC) - Morning Movers
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("morning")),
        CronTrigger(hour=13, minute=0),
        id="x_8am", name="X 8AM Morning Movers", replace_existing=True,
    )
    # 9 AM EST (14:00 UTC) - Category Spotlight: Crypto
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("spotlight_crypto")),
        CronTrigger(hour=14, minute=0),
        id="x_9am", name="X 9AM Crypto Spotlight", replace_existing=True,
    )
    # 10 AM EST (15:00 UTC) - Platform Gap
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("afternoon")),
        CronTrigger(hour=15, minute=0),
        id="x_10am", name="X 10AM Platform Gap", replace_existing=True,
    )
    # 11 AM EST (16:00 UTC) - Category Spotlight: Politics
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("spotlight_politics")),
        CronTrigger(hour=16, minute=0),
        id="x_11am", name="X 11AM Politics Spotlight", replace_existing=True,
    )
    # 12 PM EST (17:00 UTC) - Market Highlight
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("evening")),
        CronTrigger(hour=17, minute=0),
        id="x_12pm", name="X 12PM Market Highlight", replace_existing=True,
    )

    # --- AFTERNOON BLOCK (1 PM - 5 PM EST) ---
    # 1 PM EST (18:00 UTC) - Category Spotlight: Sports
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("spotlight_sports")),
        CronTrigger(hour=18, minute=0),
        id="x_1pm", name="X 1PM Sports Spotlight", replace_existing=True,
    )
    # 2 PM EST (19:00 UTC) - Platform Gap
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("afternoon")),
        CronTrigger(hour=19, minute=0),
        id="x_2pm", name="X 2PM Platform Gap", replace_existing=True,
    )
    # 3 PM EST (20:00 UTC) - Daily Poll (engagement)
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("poll")),
        CronTrigger(hour=20, minute=0),
        id="x_3pm", name="X 3PM Daily Poll", replace_existing=True,
    )
    # 4 PM EST (21:00 UTC) - Morning Movers (afternoon update)
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("morning")),
        CronTrigger(hour=21, minute=0),
        id="x_4pm", name="X 4PM Big Movers", replace_existing=True,
    )
    # 5 PM EST (22:00 UTC) - Category Spotlight: Finance
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("spotlight_finance")),
        CronTrigger(hour=22, minute=0),
        id="x_5pm", name="X 5PM Finance Spotlight", replace_existing=True,
    )

    # --- EVENING BLOCK (6 PM - 10 PM EST) ---
    # 6 PM EST (23:00 UTC) - Market Highlight
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("evening")),
        CronTrigger(hour=23, minute=0),
        id="x_6pm", name="X 6PM Market Highlight", replace_existing=True,
    )
    # 7 PM EST (00:00 UTC) - PROMO with logo
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("promo")),
        CronTrigger(hour=0, minute=0),
        id="x_7pm", name="X 7PM Daily Promo", replace_existing=True,
    )
    # 8 PM EST (01:00 UTC) - Platform Gap
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("afternoon")),
        CronTrigger(hour=1, minute=0),
        id="x_8pm", name="X 8PM Platform Gap", replace_existing=True,
    )
    # 9 PM EST (02:00 UTC) - Category Spotlight: Entertainment
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("spotlight_entertainment")),
        CronTrigger(hour=2, minute=0),
        id="x_9pm", name="X 9PM Entertainment Spotlight", replace_existing=True,
    )
    # 10 PM EST (03:00 UTC) - Market Highlight
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("evening")),
        CronTrigger(hour=3, minute=0),
        id="x_10pm", name="X 10PM Market Highlight", replace_existing=True,
    )

    # --- LATE NIGHT BLOCK (11 PM - 1 AM EST) - Gambling audience ---
    # 11 PM EST (04:00 UTC) - Sports focus (late night bettors)
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("latenight_sports")),
        CronTrigger(hour=4, minute=0),
        id="x_11pm", name="X 11PM Late Night Sports", replace_existing=True,
    )
    # 12 AM EST (05:00 UTC) - Crypto focus (24/7 market)
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("latenight_crypto")),
        CronTrigger(hour=5, minute=0),
        id="x_12am", name="X 12AM Late Night Crypto", replace_existing=True,
    )
    # 1 AM EST (06:00 UTC) - Mixed high-action markets
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("latenight_action")),
        CronTrigger(hour=6, minute=0),
        id="x_1am", name="X 1AM Late Night Action", replace_existing=True,
    )

    # --- WEEKLY ---
    # Sunday 10:00 AM EST (15:00 UTC) - Weekly Recap Thread
    scheduler.add_job(
        lambda: asyncio.create_task(post_to_x("weekly")),
        CronTrigger(day_of_week="sun", hour=15, minute=0),
        id="x_weekly_recap", name="X Weekly Recap Thread", replace_existing=True,
    )

    logger.info(f"Scheduler configured: pipeline every {interval_minutes}min, X posts hourly 8AM-1AM EST (~19/day)")
    return scheduler


async def main():
    """Main entry point for the worker.

    Modes (set via WORKER_MODE env var):
    - "continuous" (default): Run scheduler with all jobs
    - "pipeline": Run data pipeline once and exit (for Railway cron every 15min)
    - "daily": Run daily email jobs once and exit (for Railway cron at 8am)
    """
    logger.info("OddWons Worker starting...")

    mode = os.getenv("WORKER_MODE", "continuous").lower()

    # Legacy support for WORKER_RUN_ONCE
    if os.getenv("WORKER_RUN_ONCE", "false").lower() == "true":
        mode = "pipeline"

    if mode == "pipeline":
        # Railway cron mode: run pipeline once and exit
        logger.info("Running in PIPELINE mode (single execution)")
        await run_full_pipeline()
        logger.info("Pipeline complete, exiting.")

    elif mode == "daily":
        # Railway cron mode: run daily jobs once and exit
        logger.info("Running in DAILY mode (digest + trial reminders)")
        await run_daily_jobs()
        logger.info("Daily jobs complete, exiting.")

    else:
        # Continuous mode: run scheduler (recommended for Railway)
        logger.info("Running in CONTINUOUS mode (scheduler)")

        # Run pipeline immediately on startup
        run_on_start = os.getenv("WORKER_RUN_ON_START", "true").lower() == "true"
        if run_on_start:
            logger.info("Running initial pipeline on startup...")
            try:
                await run_full_pipeline()
            except Exception as e:
                logger.error(f"Initial pipeline failed: {e}")

        # Start scheduler for all subsequent jobs
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
