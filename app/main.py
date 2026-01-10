import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.core.database import init_db, close_db
from app.api.routes import markets, patterns, auth, billing, insights, cross_platform, admin
from app.services.data_collector import data_collector
from app.services.kalshi_client import kalshi_client
from app.services.polymarket_client import polymarket_client

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Scheduler for background data collection
scheduler = AsyncIOScheduler()


async def scheduled_collection():
    """Background task for collecting market data, running AI analysis, and processing alerts."""
    logger.info("Starting scheduled data collection...")
    try:
        # Step 1: Run data collection
        result = await data_collector.run_collection()
        logger.info(f"Collection complete: {result}")

        # Step 2: Run AI analysis (pattern detection + insights)
        logger.info("Starting AI analysis...")
        from app.services.patterns.engine import pattern_engine

        ai_enabled = settings.groq_api_key and len(settings.groq_api_key) > 0
        if ai_enabled:
            try:
                analysis_result = await pattern_engine.run_full_analysis(with_ai=True)
                logger.info(f"AI analysis complete: {analysis_result}")
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
        else:
            logger.warning("AI analysis skipped - GROQ_API_KEY not configured")

        # Step 3: Cross-platform matching
        logger.info("Running cross-platform market matching...")
        try:
            from app.services.market_matcher import run_market_matching
            match_result = await run_market_matching(min_volume=1000)
            logger.info(f"Market matching complete: {match_result}")
        except Exception as e:
            logger.error(f"Market matching failed: {e}")

    except Exception as e:
        logger.error(f"Scheduled collection failed: {e}", exc_info=True)


async def send_trial_reminders():
    """Send trial ending reminder emails (1 day before expiry)."""
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta
    from app.core.database import AsyncSessionLocal
    from app.models.user import User, SubscriptionStatus
    from app.services.notifications import notification_service

    logger.info("Checking for trial reminders to send...")

    async with AsyncSessionLocal() as session:
        try:
            # Find users whose trial ends in ~24 hours and haven't been reminded yet
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
    from datetime import datetime, timedelta

    logger.info("Sending daily digest emails...")

    async with AsyncSessionLocal() as session:
        try:
            # Find users with active subscriptions and digest enabled
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

            # Get today's top insights
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

            # Format insights for email
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
    from datetime import datetime
    from app.core.database import AsyncSessionLocal
    from app.models.market import Alert
    from app.models.user import User
    from app.services.notifications import notification_service

    logger.info("Processing pending alert emails...")

    async with AsyncSessionLocal() as session:
        try:
            # Find alerts that haven't been emailed yet
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.email_sent == False,
                        Alert.user_id.isnot(None)
                    )
                ).limit(50)  # Process in batches
            )
            alerts = result.scalars().all()

            if not alerts:
                logger.info("No pending alert emails")
                return

            sent_count = 0
            for alert in alerts:
                # Get the user
                user_result = await session.execute(
                    select(User).where(User.id == alert.user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user or not user.email_alerts_enabled:
                    # Mark as sent to skip in future
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
                            "score": 70  # Default score
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting OddWons API...")
    await init_db()
    logger.info("Database initialized")

    # Start scheduler
    scheduler.add_job(
        scheduled_collection,
        "interval",
        minutes=settings.collection_interval_minutes,
        id="data_collection",
        replace_existing=True,
    )

    # Trial reminder emails - daily at 10:00 AM UTC
    scheduler.add_job(
        send_trial_reminders,
        "cron",
        hour=10,
        minute=0,
        id="trial_reminders",
        replace_existing=True,
    )

    # Daily digest emails - daily at 8:00 AM UTC
    scheduler.add_job(
        send_daily_digest_emails,
        "cron",
        hour=8,
        minute=0,
        id="daily_digest",
        replace_existing=True,
    )

    # Process alert emails - every 5 minutes
    scheduler.add_job(
        process_alert_emails,
        "interval",
        minutes=5,
        id="alert_emails",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler started (collection: {settings.collection_interval_minutes} min, digest: 8am UTC, trial reminders: 10am UTC, alerts: every 5 min)")

    yield

    # Shutdown
    logger.info("Shutting down OddWons API...")
    scheduler.shutdown(wait=False)
    await kalshi_client.close()
    await polymarket_client.close()
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="OddWons API",
    description="Prediction market analysis for Kalshi and Polymarket",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(markets.router, prefix="/api/v1")
app.include_router(patterns.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")
app.include_router(cross_platform.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# ============================================================================
# ADMIN-ONLY DEBUG ENDPOINTS
# ============================================================================
from app.services.auth import require_admin, get_current_user
from app.models.user import User


@app.get("/debug/db")
async def debug_db(admin: User = Depends(require_admin)):
    """Debug database tables. ADMIN ONLY."""
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            # Check if tables exist
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            return {"status": "connected", "tables": tables}
        except Exception as e:
            return {"status": "error", "error": str(e)}


@app.get("/debug/apis")
async def debug_apis(admin: User = Depends(require_admin)):
    """Debug API clients - fetch just one page to test connectivity. ADMIN ONLY."""
    results = {"kalshi": None, "polymarket": None}

    try:
        # Test Kalshi events endpoint using the client's method
        kalshi_data = await kalshi_client.get_events(limit=1)
        results["kalshi"] = {"status": "ok", "events_count": len(kalshi_data.get("events", []))}
    except Exception as e:
        results["kalshi"] = {"status": "error", "error": str(e)}

    try:
        # Test Polymarket using its method
        poly_data = await polymarket_client.get_events(limit=1)
        results["polymarket"] = {"status": "ok", "events_count": len(poly_data)}
    except Exception as e:
        results["polymarket"] = {"status": "error", "error": str(e)}

    return results


@app.post("/debug/test-collect")
async def debug_test_collect(admin: User = Depends(require_admin)):
    """Test collecting just a few markets to debug collection issues."""
    from app.core.database import AsyncSessionLocal
    from app.models.market import Market, Platform
    from sqlalchemy.dialects.postgresql import insert
    from datetime import datetime

    results = {"kalshi": None, "polymarket": None, "markets_before": 0, "markets_after": 0}

    async with AsyncSessionLocal() as session:
        # Count before
        from sqlalchemy import select, func
        count_before = await session.scalar(select(func.count()).select_from(Market))
        results["markets_before"] = count_before or 0

        # Try Kalshi
        try:
            kalshi_markets = await kalshi_client.fetch_all_markets(max_pages=1)
            results["kalshi"] = {"fetched": len(kalshi_markets)}

            for market_data in kalshi_markets:  # All from first page
                market_id = f"kalshi_{market_data.ticker}"
                yes_price = market_data.yes_ask if market_data.yes_ask else market_data.yes_bid
                stmt = insert(Market).values(
                    id=market_id,
                    platform=Platform.KALSHI,
                    title=market_data.title,
                    description=market_data.subtitle,
                    category=market_data.category,
                    yes_price=yes_price,
                    volume=market_data.volume,
                    status=market_data.status,
                ).on_conflict_do_update(
                    index_elements=["id"],
                    set_={"yes_price": yes_price, "updated_at": datetime.utcnow()}
                )
                await session.execute(stmt)

            await session.commit()
            results["kalshi"]["saved"] = len(kalshi_markets)
        except Exception as e:
            results["kalshi"] = {"error": str(e)}
            await session.rollback()

        # Try Polymarket
        try:
            poly_markets = await polymarket_client.fetch_all_markets(max_pages=1)
            results["polymarket"] = {"fetched": len(poly_markets)}

            for market_data in poly_markets:
                if not market_data.condition_id:
                    continue
                market_id = f"poly_{market_data.condition_id}"
                yes_price = market_data.outcome_prices[0] if market_data.outcome_prices else None
                stmt = insert(Market).values(
                    id=market_id,
                    platform=Platform.POLYMARKET,
                    title=market_data.question,
                    description=market_data.description,
                    category=market_data.category,
                    yes_price=yes_price,
                    volume=market_data.volume,
                    status="active",
                ).on_conflict_do_update(
                    index_elements=["id"],
                    set_={"yes_price": yes_price, "updated_at": datetime.utcnow()}
                )
                await session.execute(stmt)

            await session.commit()
            results["polymarket"]["saved"] = len([m for m in poly_markets if m.condition_id])
        except Exception as e:
            results["polymarket"] = {"error": str(e)}
            await session.rollback()

        # Count after
        count_after = await session.scalar(select(func.count()).select_from(Market))
        results["markets_after"] = count_after or 0

    return results


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OddWons API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/api/v1/collect")
async def trigger_collection(admin: User = Depends(require_admin)):
    """Manually trigger data collection. ADMIN ONLY."""
    result = await data_collector.run_collection()
    return {"status": "completed", "result": result}


@app.post("/api/v1/analyze")
async def trigger_analysis(admin: User = Depends(require_admin)):
    """Manually trigger AI analysis (generates fresh insights). ADMIN ONLY."""
    from app.services.patterns.engine import pattern_engine

    try:
        result = await pattern_engine.run_full_analysis(with_ai=True)
        return {"status": "completed", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/debug/migrate")
async def run_migrations(admin: User = Depends(require_admin)):
    """Add missing columns to database tables. ADMIN ONLY."""
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal

    results = {"alerts": [], "users": []}

    async with AsyncSessionLocal() as session:
        # Check alerts columns
        result = await session.execute(text('''
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
        '''), {'table_name': 'alerts'})
        alert_cols = [row[0] for row in result.fetchall()]

        if 'user_id' not in alert_cols:
            await session.execute(text('ALTER TABLE alerts ADD COLUMN user_id VARCHAR REFERENCES users(id)'))
            results["alerts"].append("added user_id")

        if 'email_sent' not in alert_cols:
            await session.execute(text('ALTER TABLE alerts ADD COLUMN email_sent BOOLEAN DEFAULT FALSE'))
            results["alerts"].append("added email_sent")

        if 'email_sent_at' not in alert_cols:
            await session.execute(text('ALTER TABLE alerts ADD COLUMN email_sent_at TIMESTAMP'))
            results["alerts"].append("added email_sent_at")

        # Check users columns
        result = await session.execute(text('''
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
        '''), {'table_name': 'users'})
        user_cols = [row[0] for row in result.fetchall()]

        if 'email_alerts_enabled' not in user_cols:
            await session.execute(text('ALTER TABLE users ADD COLUMN email_alerts_enabled BOOLEAN DEFAULT TRUE'))
            results["users"].append("added email_alerts_enabled")

        if 'email_digest_enabled' not in user_cols:
            await session.execute(text('ALTER TABLE users ADD COLUMN email_digest_enabled BOOLEAN DEFAULT TRUE'))
            results["users"].append("added email_digest_enabled")

        if 'trial_reminder_sent' not in user_cols:
            await session.execute(text('ALTER TABLE users ADD COLUMN trial_reminder_sent BOOLEAN DEFAULT FALSE'))
            results["users"].append("added trial_reminder_sent")

        if 'trial_start' not in user_cols:
            await session.execute(text('ALTER TABLE users ADD COLUMN trial_start TIMESTAMP'))
            results["users"].append("added trial_start")

        # Check markets columns
        result = await session.execute(text('''
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
        '''), {'table_name': 'markets'})
        market_cols = [row[0] for row in result.fetchall()]
        results["markets"] = []

        if 'image_url' not in market_cols:
            await session.execute(text('ALTER TABLE markets ADD COLUMN image_url VARCHAR'))
            results["markets"].append("added image_url")

        await session.commit()

    if not results["alerts"] and not results["users"] and not results.get("markets"):
        return {"status": "no changes needed", "alerts": alert_cols, "users": user_cols, "markets": market_cols}

    return {"status": "migrations applied", "changes": results}
