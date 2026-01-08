from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

# SQLAlchemy async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """Dependency for getting Redis connection."""
    return redis.Redis(connection_pool=redis_pool)


async def init_db():
    """Initialize database tables."""
    # Import all models so they're registered with Base.metadata
    from app.models import market, user, ai_insight, cross_platform_match  # noqa

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()
