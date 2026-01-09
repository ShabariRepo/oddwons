# Prediction Market APIs Reference

> **When to use this skill:** When working on data collection, API clients, or market data fetching for Kalshi or Polymarket.

## Quick Reference

| Platform | Base URL | Auth Required | Rate Limit |
|----------|----------|---------------|------------|
| Kalshi | `https://api.elections.kalshi.com/trade-api/v2` | No (read-only) | ~100/min |
| Polymarket Gamma | `https://gamma-api.polymarket.com` | No | ~100/min |
| Polymarket CLOB | `https://clob.polymarket.com` | No | ~100/min |
| Polymarket Data | `https://data-api.polymarket.com` | No | ~100/min |

---

## KALSHI API

### Get Events (PRIMARY - Use this for political/economic markets)
```
GET /events
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | 1-200, default 100 |
| `cursor` | string | Pagination cursor |
| `status` | string | `open`, `closed`, `settled` |
| `series_ticker` | string | Filter by series |
| `with_nested_markets` | bool | Include markets in response |

**Response:**
```json
{
  "events": [{
    "event_ticker": "FEDCHAIR-25",
    "series_ticker": "FEDCHAIR",
    "title": "Who will be the next Fed Chair?",
    "sub_title": "...",
    "category": "Economics",
    "mutually_exclusive": true,
    "strike_date": "2025-05-15T00:00:00Z",
    "markets": [...]  // if with_nested_markets=true
  }],
  "cursor": "next_page_cursor"
}
```

### Get Markets
```
GET /markets
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | 1-1000, default 100 |
| `cursor` | string | Pagination |
| `event_ticker` | string | Filter by event |
| `series_ticker` | string | Filter by series |
| `status` | string | `open`, `closed`, `settled` |
| `tickers` | string | Comma-separated market tickers |

**Response:**
```json
{
  "markets": [{
    "ticker": "FEDCHAIR-25-WARSH",
    "event_ticker": "FEDCHAIR-25",
    "title": "Kevin Warsh to be nominated as Fed Chair?",
    "subtitle": "...",
    "yes_sub_title": "Warsh nominated",
    "no_sub_title": "Not Warsh",
    "status": "open",
    "yes_bid": 41,           // ⚠️ IN CENTS (0-100)
    "yes_ask": 42,
    "no_bid": 58,
    "no_ask": 59,
    "last_price": 41,
    "volume": 3291774,       // Total volume in cents
    "volume_24h": 150000,
    "open_interest": 50000,
    "close_time": "2025-05-15T00:00:00Z",
    "expiration_time": "2025-05-16T00:00:00Z"
  }],
  "cursor": "..."
}
```

**⚠️ CRITICAL: Kalshi prices are in CENTS (0-100). Convert to decimal: `price / 100`**

### Get Event Metadata (FOR IMAGES)
```
GET /events/{event_ticker}/metadata
```

**Response:**
```json
{
  "image_url": "https://kalshi-images.s3.amazonaws.com/...",
  "featured_image_url": "https://...",
  "market_details": [{
    "market_ticker": "FEDCHAIR-25-WARSH",
    "image_url": "https://...",
    "color_code": "#1E88E5"
  }],
  "settlement_sources": [{
    "name": "Federal Reserve",
    "url": "https://federalreserve.gov"
  }]
}
```

### Get Market Candlesticks (Price History)
```
GET /markets/{ticker}/candlesticks
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `start_ts` | int | Unix timestamp |
| `end_ts` | int | Unix timestamp |
| `period_interval` | int | Seconds (60, 3600, 86400) |

---

## POLYMARKET API

### Gamma API - Get Events (PRIMARY)
```
GET https://gamma-api.polymarket.com/events
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Default 100 |
| `offset` | int | Pagination offset |
| `closed` | bool | `false` for active markets |
| `order` | string | `id`, `volume`, etc. |
| `ascending` | bool | Sort direction |
| `tag_id` | int | Filter by tag/category |

**Response:**
```json
[{
  "id": "12345",
  "slug": "fed-chair-nomination",
  "title": "Who will Trump nominate as Fed Chair?",
  "description": "...",
  "startDate": "2024-12-01T00:00:00Z",
  "endDate": "2025-05-15T00:00:00Z",
  "image": "https://polymarket-upload.s3.amazonaws.com/fed.png",
  "icon": "https://polymarket-upload.s3.amazonaws.com/fed-icon.png",
  "active": true,
  "closed": false,
  "volume": 6867281.50,        // ⚠️ IN DOLLARS (not cents)
  "volume24hr": 150000.00,
  "liquidity": 250000.00,
  "markets": [{
    "id": "0x123...",
    "question": "Kevin Warsh?",
    "outcomePrices": "[\"0.385\", \"0.615\"]",  // ⚠️ Stringified JSON!
    "outcomes": "[\"Yes\", \"No\"]",
    "volume": 3575507.25,
    "clobTokenIds": "[\"token1\", \"token2\"]"
  }],
  "tags": [{"id": "100123", "label": "Politics", "slug": "politics"}]
}]
```

**⚠️ CRITICAL: `outcomePrices` and `outcomes` are STRINGIFIED JSON - must parse!**

### Gamma API - Get Markets
```
GET https://gamma-api.polymarket.com/markets
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Default 100 |
| `offset` | int | Pagination |
| `closed` | bool | `false` for active |
| `tag_id` | int | Category filter |

**Response:**
```json
[{
  "id": "0x3b04d48550593c604c7022e51b5738cf889b44a5",
  "question": "Will Kevin Warsh be nominated as Fed Chair?",
  "conditionId": "0x...",
  "slug": "kevin-warsh-fed-chair",
  "outcomePrices": "[\"0.385\", \"0.615\"]",
  "outcomes": "[\"Yes\", \"No\"]",
  "volume": 3575507.25,
  "volume24hr": 75000.00,
  "liquidity": 125000.00,
  "startDate": "2024-12-01",
  "endDate": "2025-05-15",
  "image": "https://polymarket-upload.s3.amazonaws.com/warsh.png",
  "icon": "https://polymarket-upload.s3.amazonaws.com/warsh-icon.png",
  "description": "...",
  "tags": [...]
}]
```

### CLOB API - Get Price
```
GET https://clob.polymarket.com/price
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `token_id` | string | CLOB token ID |
| `side` | string | `buy` or `sell` |

**Response:**
```json
{
  "price": "0.385"
}
```

### CLOB API - Get Order Book
```
GET https://clob.polymarket.com/book
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `token_id` | string | CLOB token ID |

**Response:**
```json
{
  "market": "0x...",
  "asset_id": "token123",
  "bids": [{"price": "0.38", "size": "1000"}],
  "asks": [{"price": "0.39", "size": "500"}],
  "timestamp": "2025-01-05T12:00:00Z"
}
```

### Data API - Price History
```
GET https://data-api.polymarket.com/prices-history
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `market` | string | Market ID |
| `interval` | string | `1h`, `1d`, `1w` |
| `fidelity` | int | Data points |

---

## Common Patterns

### Fetching All Active Markets

**Kalshi:**
```python
async def fetch_all_kalshi_markets():
    markets = []
    cursor = None
    while True:
        params = {"limit": 1000, "status": "open"}
        if cursor:
            params["cursor"] = cursor
        response = await client.get("/markets", params=params)
        data = response.json()
        markets.extend(data["markets"])
        cursor = data.get("cursor")
        if not cursor:
            break
    return markets
```

**Polymarket:**
```python
async def fetch_all_polymarket_events():
    events = []
    offset = 0
    while True:
        params = {"limit": 100, "offset": offset, "closed": "false"}
        response = await client.get("/events", params=params)
        data = response.json()
        if not data:
            break
        events.extend(data)
        offset += len(data)
        if len(data) < 100:
            break
    return events
```

### Parsing Polymarket Prices

```python
import json

def parse_polymarket_market(market: dict) -> dict:
    """Parse stringified fields in Polymarket response."""
    # These fields come as strings like '["0.385", "0.615"]'
    if "outcomePrices" in market and isinstance(market["outcomePrices"], str):
        prices = json.loads(market["outcomePrices"])
        market["yes_price"] = float(prices[0])
        market["no_price"] = float(prices[1])
    
    if "outcomes" in market and isinstance(market["outcomes"], str):
        market["outcomes"] = json.loads(market["outcomes"])
    
    if "clobTokenIds" in market and isinstance(market["clobTokenIds"], str):
        market["clobTokenIds"] = json.loads(market["clobTokenIds"])
    
    return market
```

### Converting Kalshi Cents to Decimal

```python
def kalshi_cents_to_decimal(cents: int) -> float:
    """Convert Kalshi cents (0-100) to decimal (0-1)."""
    if cents is None:
        return None
    return cents / 100.0

# Usage:
market["yes_price"] = kalshi_cents_to_decimal(raw["yes_bid"])  # 41 -> 0.41
```

---

## Key Differences

| Aspect | Kalshi | Polymarket |
|--------|--------|------------|
| Prices | Cents (0-100) | Decimal (0-1) |
| Volume | Cents | Dollars |
| Pagination | Cursor-based | Offset-based |
| Nested data | Clean JSON | Stringified JSON |
| Images | Separate `/metadata` call | Inline `image`/`icon` fields |
| Categories | `category` field | `tags` array |
| Market ID | `ticker` (string) | `id` (hex address) |

---

## Fields to Store

For oddwons database, collect these fields:

```python
market_data = {
    # Core
    "id": str,              # Platform-specific ID
    "platform": str,        # "KALSHI" or "POLYMARKET"
    "title": str,
    "description": str,
    
    # Pricing (normalized to decimal 0-1)
    "yes_price": float,
    "no_price": float,
    
    # Volume (normalized to dollars)
    "volume": float,
    "volume_24h": float,
    
    # Liquidity
    "liquidity": float,
    "open_interest": float,
    
    # Timing
    "close_time": datetime,
    "status": str,          # "active", "closed", "resolved"
    
    # Categorization
    "category": str,
    "tags": list,
    
    # Images
    "image_url": str,
    
    # Platform links
    "platform_url": str,
}
```

---

## Error Handling

```python
# Both APIs return standard HTTP errors
# 429 = Rate limited (back off exponentially)
# 404 = Market/event not found
# 500 = Server error (retry with backoff)

async def fetch_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = await client.get(url)
            if response.status_code == 429:
                await asyncio.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```
