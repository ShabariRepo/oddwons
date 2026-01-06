import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
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
    """Background task for collecting market data."""
    logger.info("Starting scheduled data collection...")
    try:
        result = await data_collector.run_collection()
        logger.info(f"Collection complete: {result}")
    except Exception as e:
        logger.error(f"Scheduled collection failed: {e}")


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
    scheduler.start()
    logger.info(f"Scheduler started (interval: {settings.collection_interval_minutes} min)")

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
async def trigger_collection():
    """Manually trigger data collection."""
    result = await data_collector.run_collection()
    return {"status": "completed", "result": result}
