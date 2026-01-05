import httpx
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.config import get_settings
from app.schemas.market import PolymarketMarketData

logger = logging.getLogger(__name__)
settings = get_settings()


class PolymarketClient:
    """Direct API client for Polymarket prediction markets."""

    def __init__(self):
        self.gamma_url = settings.polymarket_gamma_url
        self.clob_url = settings.polymarket_clob_url
        self.api_key = settings.polymarket_api_key
        self._gamma_client: Optional[httpx.AsyncClient] = None
        self._clob_client: Optional[httpx.AsyncClient] = None

    async def _get_gamma_client(self) -> httpx.AsyncClient:
        """Client for Gamma API (market discovery)."""
        if self._gamma_client is None:
            self._gamma_client = httpx.AsyncClient(
                base_url=self.gamma_url,
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )
        return self._gamma_client

    async def _get_clob_client(self) -> httpx.AsyncClient:
        """Client for CLOB API (orderbook/pricing)."""
        if self._clob_client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._clob_client = httpx.AsyncClient(
                base_url=self.clob_url,
                headers=headers,
                timeout=30.0,
            )
        return self._clob_client

    async def close(self):
        if self._gamma_client:
            await self._gamma_client.aclose()
            self._gamma_client = None
        if self._clob_client:
            await self._clob_client.aclose()
            self._clob_client = None

    async def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        closed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch events from Gamma API.

        Note: Use closed=False to get open/tradeable markets.
        The 'active' param means 'not archived', NOT 'open for trading'.
        """
        client = await self._get_gamma_client()
        params = {
            "limit": limit,
            "offset": offset,
            "closed": str(closed).lower(),
        }

        try:
            response = await client.get("/events", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Polymarket Gamma API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Polymarket client error: {e}")
            raise

    async def get_markets(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch markets from Gamma API."""
        client = await self._get_gamma_client()
        params = {"limit": limit, "offset": offset}

        try:
            response = await client.get("/markets", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Polymarket markets error: {e}")
            raise

    async def get_market_prices(self, token_id: str) -> Dict[str, Any]:
        """Fetch current prices from CLOB API."""
        client = await self._get_clob_client()
        try:
            response = await client.get(f"/prices", params={"token_ids": token_id})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Polymarket prices error for {token_id}: {e}")
            raise

    async def get_orderbook(self, token_id: str) -> Dict[str, Any]:
        """Fetch orderbook from CLOB API."""
        client = await self._get_clob_client()
        try:
            response = await client.get(f"/book", params={"token_id": token_id})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Polymarket orderbook error for {token_id}: {e}")
            raise

    def parse_market(self, event: Dict[str, Any]) -> List[PolymarketMarketData]:
        """Parse event data into market data objects."""
        markets = []

        # Event-level volume24hr (applies to all markets in this event)
        event_volume_24h = float(event.get("volume24hr", 0) or 0)

        for market in event.get("markets", [event]):
            try:
                outcomes = []
                prices = []

                # Extract outcomes - API returns JSON strings like "[\"Yes\", \"No\"]"
                if "outcomes" in market:
                    raw_outcomes = market["outcomes"]
                    if isinstance(raw_outcomes, str):
                        try:
                            outcomes = json.loads(raw_outcomes)
                        except json.JSONDecodeError:
                            outcomes = [raw_outcomes]
                    elif isinstance(raw_outcomes, list):
                        outcomes = raw_outcomes

                # Extract prices - API returns JSON strings like "[\"0.65\", \"0.35\"]"
                if "outcomePrices" in market:
                    raw_prices = market["outcomePrices"]
                    if isinstance(raw_prices, str):
                        try:
                            parsed = json.loads(raw_prices)
                            prices = [float(p) for p in parsed]
                        except (json.JSONDecodeError, ValueError):
                            prices = []
                    elif isinstance(raw_prices, list):
                        prices = [float(p) for p in raw_prices]
                elif "outcome_prices" in market:
                    raw_prices = market["outcome_prices"]
                    if isinstance(raw_prices, str):
                        try:
                            parsed = json.loads(raw_prices)
                            prices = [float(p) for p in parsed]
                        except (json.JSONDecodeError, ValueError):
                            prices = []
                    elif isinstance(raw_prices, list):
                        prices = [float(p) for p in raw_prices]

                # Parse spread - can be a string like "0.01"
                spread = None
                if market.get("spread"):
                    try:
                        spread = float(market["spread"])
                    except (ValueError, TypeError):
                        pass

                # Parse best ask
                best_ask = None
                if market.get("bestAsk"):
                    try:
                        best_ask = float(market["bestAsk"])
                    except (ValueError, TypeError):
                        pass

                # Parse 24h price change (percentage)
                price_change_24h = None
                if market.get("oneDayPriceChange") is not None:
                    try:
                        price_change_24h = float(market["oneDayPriceChange"])
                    except (ValueError, TypeError):
                        pass

                markets.append(PolymarketMarketData(
                    condition_id=market.get("conditionId", market.get("condition_id", "")),
                    question=market.get("question", event.get("title", "")),
                    description=market.get("description"),
                    outcomes=outcomes,
                    outcome_prices=prices,
                    volume=float(market.get("volume", 0) or 0),
                    volume_24h=event_volume_24h,  # Event-level 24h volume
                    volume_1wk=float(market.get("volume1wk", 0) or 0),
                    liquidity=float(market.get("liquidity", 0) or 0),
                    end_date=datetime.fromisoformat(market["endDate"].replace("Z", "+00:00")) if market.get("endDate") else None,
                    category=event.get("category"),
                    spread=spread,
                    best_ask=best_ask,
                    price_change_24h=price_change_24h,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse Polymarket market: {e}")

        return markets

    async def fetch_all_markets(self, max_pages: int = 100) -> List[PolymarketMarketData]:
        """Fetch all open markets with pagination and rate limiting."""
        all_markets = []
        offset = 0
        limit = 100
        page = 0

        while page < max_pages:
            try:
                events = await self.get_events(limit=limit, offset=offset, closed=False)

                if not events:
                    break

                for event in events:
                    all_markets.extend(self.parse_market(event))

                if len(events) < limit:
                    break

                offset += limit
                page += 1

                # Rate limiting: 0.2 second delay between requests
                await asyncio.sleep(0.2)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - wait and retry
                    logger.warning("Polymarket rate limited, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                raise

        logger.info(f"Fetched {len(all_markets)} markets from Polymarket ({page} pages)")
        return all_markets


# Singleton instance
polymarket_client = PolymarketClient()
