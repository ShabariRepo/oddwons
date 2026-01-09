import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.config import get_settings
from app.schemas.market import KalshiMarketData

logger = logging.getLogger(__name__)
settings = get_settings()


class KalshiClient:
    """Direct API client for Kalshi prediction markets."""

    def __init__(self):
        self.base_url = settings.kalshi_base_url
        self.api_key = settings.kalshi_api_key
        self.api_secret = settings.kalshi_api_secret
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_markets(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        status: str = "open",
    ) -> Dict[str, Any]:
        """Fetch list of markets from Kalshi."""
        client = await self._get_client()
        params = {
            "limit": limit,
            "status": status,
        }
        if cursor:
            params["cursor"] = cursor

        try:
            response = await client.get("/markets", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Kalshi API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Kalshi client error: {e}")
            raise

    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """Fetch single market by ticker."""
        client = await self._get_client()
        try:
            response = await client.get(f"/markets/{ticker}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Kalshi API error for {ticker}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Kalshi client error: {e}")
            raise

    async def get_market_orderbook(self, ticker: str) -> Dict[str, Any]:
        """Fetch orderbook for a market."""
        client = await self._get_client()
        try:
            response = await client.get(f"/markets/{ticker}/orderbook")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Kalshi orderbook error for {ticker}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Kalshi client error: {e}")
            raise

    async def get_events(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        status: str = "open",
    ) -> Dict[str, Any]:
        """Fetch events (groupings of markets) - these contain the political/economic markets."""
        client = await self._get_client()
        params = {"limit": limit, "status": status}
        if cursor:
            params["cursor"] = cursor
        try:
            response = await client.get("/events", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Kalshi events error: {e}")
            raise

    async def get_event_markets(self, event_ticker: str) -> Dict[str, Any]:
        """Fetch event details including its markets."""
        client = await self._get_client()
        try:
            # The /events/{ticker} endpoint returns {'event': {...}, 'markets': [...]}
            response = await client.get(f"/events/{event_ticker}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Kalshi event markets error for {event_ticker}: {e}")
            raise

    def parse_market(self, data: Dict[str, Any], event_image_url: Optional[str] = None) -> KalshiMarketData:
        """Parse raw API response into structured data.

        Note: Kalshi API returns prices in cents (0-100), we convert to decimal (0-1)
        to match Polymarket format.
        """
        market = data.get("market", data)

        # Convert cents to decimal (divide by 100)
        def cents_to_decimal(val):
            if val is None:
                return None
            return val / 100.0

        # Try to get image URL from market, event, or passed-in event_image_url
        image_url = (
            market.get("image_url") or
            market.get("event_image_url") or
            market.get("strike_period_image") or
            event_image_url
        )

        return KalshiMarketData(
            ticker=market.get("ticker", ""),
            title=market.get("title", ""),
            subtitle=market.get("subtitle"),
            yes_bid=cents_to_decimal(market.get("yes_bid")),
            yes_ask=cents_to_decimal(market.get("yes_ask")),
            no_bid=cents_to_decimal(market.get("no_bid")),
            no_ask=cents_to_decimal(market.get("no_ask")),
            volume=market.get("volume"),
            open_interest=market.get("open_interest"),
            status=market.get("status", "unknown"),
            close_time=datetime.fromisoformat(market["close_time"]) if market.get("close_time") else None,
            category=market.get("category"),
            image_url=image_url,
        )

    async def fetch_all_markets(self, max_pages: int = 50) -> List[KalshiMarketData]:
        """Fetch all open markets from both /markets and /events endpoints.

        The /markets endpoint returns sports parlays.
        The /events endpoint returns political/economic prediction markets.
        We fetch from both to get comprehensive coverage.
        """
        all_markets = []
        seen_tickers = set()

        # 1. Fetch from /events endpoint (political/economic markets)
        logger.info("Fetching Kalshi events (political/economic markets)...")
        cursor = None
        page = 0

        while page < max_pages:
            try:
                result = await self.get_events(limit=100, cursor=cursor)
                events = result.get("events", [])

                for event in events:
                    event_ticker = event.get("event_ticker") or event.get("ticker")
                    if not event_ticker:
                        continue

                    # Extract event image URL
                    event_image_url = event.get("image_url") or event.get("image")

                    # Get markets for this event
                    try:
                        event_markets = await self.get_event_markets(event_ticker)
                        markets = event_markets.get("markets", [])

                        # Also try to get image from event detail
                        event_detail = event_markets.get("event", {})
                        if not event_image_url:
                            event_image_url = event_detail.get("image_url") or event_detail.get("image")

                        for m in markets:
                            ticker = m.get("ticker", "")
                            if ticker in seen_tickers:
                                continue
                            seen_tickers.add(ticker)

                            try:
                                parsed = self.parse_market(m, event_image_url=event_image_url)
                                # Add category from event
                                parsed.category = event.get("category")
                                all_markets.append(parsed)
                            except Exception as e:
                                logger.warning(f"Failed to parse market: {e}")

                        await asyncio.sleep(0.2)  # Rate limit between event market fetches
                    except Exception as e:
                        logger.warning(f"Failed to fetch markets for event {event_ticker}: {e}")

                cursor = result.get("cursor")
                if not cursor or not events:
                    break

                page += 1
                await asyncio.sleep(0.5)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning("Kalshi rate limited, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                raise

        event_count = len(all_markets)
        logger.info(f"Fetched {event_count} markets from Kalshi events")

        # 2. Fetch from /markets endpoint (sports parlays) - limit to avoid duplicates
        logger.info("Fetching Kalshi markets (sports)...")
        cursor = None
        page = 0

        while page < min(max_pages, 10):  # Limit sports to 10 pages
            try:
                result = await self.get_markets(limit=100, cursor=cursor)
                markets = result.get("markets", [])

                for m in markets:
                    ticker = m.get("ticker", "")
                    if ticker in seen_tickers:
                        continue
                    seen_tickers.add(ticker)

                    try:
                        all_markets.append(self.parse_market(m))
                    except Exception as e:
                        logger.warning(f"Failed to parse market: {e}")

                cursor = result.get("cursor")
                if not cursor or not markets:
                    break

                page += 1
                await asyncio.sleep(0.5)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning("Kalshi rate limited, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                raise

        logger.info(f"Fetched {len(all_markets)} total markets from Kalshi ({event_count} from events)")
        return all_markets


# Singleton instance
kalshi_client = KalshiClient()
