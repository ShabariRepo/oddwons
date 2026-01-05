import logging
from datetime import datetime, timezone
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
import redis.asyncio as redis

from app.core.database import AsyncSessionLocal, get_redis
from app.models.market import Market, MarketSnapshot, Platform
from app.services.kalshi_client import kalshi_client
from app.services.polymarket_client import polymarket_client

logger = logging.getLogger(__name__)


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert timezone-aware datetime to naive UTC datetime for database storage."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and strip timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class DataCollector:
    """Service for collecting and storing market data."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def collect_kalshi_markets(self, session: AsyncSession) -> int:
        """Collect markets from Kalshi and store in database."""
        try:
            markets = await kalshi_client.fetch_all_markets()
            count = 0

            for market_data in markets:
                # Upsert market
                market_id = f"kalshi_{market_data.ticker}"
                yes_price = market_data.yes_ask if market_data.yes_ask else market_data.yes_bid
                no_price = market_data.no_ask if market_data.no_ask else market_data.no_bid

                stmt = insert(Market).values(
                    id=market_id,
                    platform=Platform.KALSHI,
                    title=market_data.title,
                    description=market_data.subtitle,
                    category=market_data.category,
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=market_data.volume,
                    status=market_data.status,
                    close_time=to_naive_utc(market_data.close_time),
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "yes_price": stmt.excluded.yes_price,
                        "no_price": stmt.excluded.no_price,
                        "volume": stmt.excluded.volume,
                        "status": stmt.excluded.status,
                        "updated_at": datetime.utcnow(),
                    }
                )
                await session.execute(stmt)

                # Create snapshot
                snapshot = MarketSnapshot(
                    market_id=market_id,
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=market_data.volume,
                    best_bid=market_data.yes_bid,
                    best_ask=market_data.yes_ask,
                    spread=(market_data.yes_ask - market_data.yes_bid) if market_data.yes_ask and market_data.yes_bid else None,
                )
                session.add(snapshot)

                # Cache in Redis
                r = await self.get_redis()
                await r.hset(
                    f"market:{market_id}",
                    mapping={
                        "yes_price": str(yes_price or 0),
                        "no_price": str(no_price or 0),
                        "volume": str(market_data.volume or 0),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                await r.expire(f"market:{market_id}", 3600)  # 1 hour TTL

                count += 1

            await session.commit()
            logger.info(f"Collected {count} Kalshi markets")
            return count

        except Exception as e:
            logger.error(f"Error collecting Kalshi markets: {e}")
            await session.rollback()
            raise

    async def collect_polymarket_markets(self, session: AsyncSession) -> int:
        """Collect markets from Polymarket and store in database."""
        try:
            markets = await polymarket_client.fetch_all_markets()
            count = 0

            for market_data in markets:
                if not market_data.condition_id:
                    continue

                market_id = f"poly_{market_data.condition_id}"

                # Get yes/no prices from outcomes
                yes_price = None
                no_price = None
                if len(market_data.outcome_prices) >= 2:
                    yes_price = market_data.outcome_prices[0]
                    no_price = market_data.outcome_prices[1]
                elif len(market_data.outcome_prices) == 1:
                    yes_price = market_data.outcome_prices[0]

                stmt = insert(Market).values(
                    id=market_id,
                    platform=Platform.POLYMARKET,
                    title=market_data.question,
                    description=market_data.description,
                    category=market_data.category,
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=market_data.volume,
                    liquidity=market_data.liquidity,
                    status="active",
                    close_time=to_naive_utc(market_data.end_date),
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "yes_price": stmt.excluded.yes_price,
                        "no_price": stmt.excluded.no_price,
                        "volume": stmt.excluded.volume,
                        "liquidity": stmt.excluded.liquidity,
                        "updated_at": datetime.utcnow(),
                    }
                )
                await session.execute(stmt)

                # Create snapshot
                snapshot = MarketSnapshot(
                    market_id=market_id,
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=market_data.volume,
                )
                session.add(snapshot)

                # Cache in Redis
                r = await self.get_redis()
                await r.hset(
                    f"market:{market_id}",
                    mapping={
                        "yes_price": str(yes_price or 0),
                        "no_price": str(no_price or 0),
                        "volume": str(market_data.volume or 0),
                        "liquidity": str(market_data.liquidity or 0),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                await r.expire(f"market:{market_id}", 3600)

                count += 1

            await session.commit()
            logger.info(f"Collected {count} Polymarket markets")
            return count

        except Exception as e:
            logger.error(f"Error collecting Polymarket markets: {e}")
            await session.rollback()
            raise

    async def run_collection(self, run_pattern_detection: bool = True) -> dict:
        """Run full data collection from all platforms."""
        results = {"kalshi": 0, "polymarket": 0, "patterns": 0, "errors": []}

        async with AsyncSessionLocal() as session:
            try:
                results["kalshi"] = await self.collect_kalshi_markets(session)
            except Exception as e:
                results["errors"].append(f"Kalshi: {str(e)}")
                logger.error(f"Kalshi collection failed: {e}")

            try:
                results["polymarket"] = await self.collect_polymarket_markets(session)
            except Exception as e:
                results["errors"].append(f"Polymarket: {str(e)}")
                logger.error(f"Polymarket collection failed: {e}")

        # Run pattern detection after data collection
        if run_pattern_detection:
            try:
                from app.services.patterns.engine import pattern_engine
                analysis = await pattern_engine.run_full_analysis()
                results["patterns"] = analysis.get("total_patterns_detected", 0)
                results["patterns_saved"] = analysis.get("patterns_saved", 0)
                logger.info(f"Pattern detection found {results['patterns']} patterns")
            except Exception as e:
                results["errors"].append(f"Pattern detection: {str(e)}")
                logger.error(f"Pattern detection failed: {e}")

        # Update last collection timestamp
        r = await self.get_redis()
        await r.set("last_collection", datetime.utcnow().isoformat())

        logger.info(f"Data collection complete: {results}")
        return results


# Singleton instance
data_collector = DataCollector()
