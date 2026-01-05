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

    async def get_events(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch events (groupings of markets)."""
        client = await self._get_client()
        try:
            response = await client.get("/events", params={"limit": limit})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Kalshi events error: {e}")
            raise

    def parse_market(self, data: Dict[str, Any]) -> KalshiMarketData:
        """Parse raw API response into structured data."""
        market = data.get("market", data)
        return KalshiMarketData(
            ticker=market.get("ticker", ""),
            title=market.get("title", ""),
            subtitle=market.get("subtitle"),
            yes_bid=market.get("yes_bid"),
            yes_ask=market.get("yes_ask"),
            no_bid=market.get("no_bid"),
            no_ask=market.get("no_ask"),
            volume=market.get("volume"),
            open_interest=market.get("open_interest"),
            status=market.get("status", "unknown"),
            close_time=datetime.fromisoformat(market["close_time"]) if market.get("close_time") else None,
            category=market.get("category"),
        )

    async def fetch_all_markets(self, max_pages: int = 50) -> List[KalshiMarketData]:
        """Fetch all open markets with pagination and rate limiting."""
        all_markets = []
        cursor = None
        page = 0

        while page < max_pages:
            try:
                result = await self.get_markets(limit=100, cursor=cursor)
                markets = result.get("markets", [])

                for m in markets:
                    try:
                        all_markets.append(self.parse_market(m))
                    except Exception as e:
                        logger.warning(f"Failed to parse market: {e}")

                cursor = result.get("cursor")
                if not cursor or not markets:
                    break

                page += 1
                # Rate limiting: 0.5 second delay between requests to avoid 429
                await asyncio.sleep(0.5)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - wait and retry
                    logger.warning("Kalshi rate limited, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                raise

        logger.info(f"Fetched {len(all_markets)} markets from Kalshi ({page} pages)")
        return all_markets


# Singleton instance
kalshi_client = KalshiClient()
