# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OddWons is a subscription-based prediction market analysis app that analyzes Kalshi and Polymarket markets using AI agents to identify betting opportunities, patterns, and market inefficiencies.

## API Integration

### Kalshi API
- Base URL: `https://api.elections.kalshi.com/trade-api/v2`
- Key endpoints: `/markets`, `/markets/trades`, `/events`
- WebSocket available for real-time streaming

### Polymarket API
- Gamma API: `https://gamma-api.polymarket.com/events` (market discovery)
- CLOB API: `https://clob.polymarket.com/` (pricing, orderbook)
- GraphQL subgraph available for aggregate queries
- WebSocket for real-time orderbook updates

### MCP Servers (Recommended Approach)
- Multi-platform: https://www.pulsemcp.com/servers/jamesanz-prediction-markets (covers Kalshi, Polymarket, PredictIt)
- Polymarket Rust: https://github.com/ozgureyilmaz/polymarket-mcp

## Architecture

### Data Strategy
- Batch data collection every 15-30 minutes stored in PostgreSQL
- Batch analysis on stored data (avoids rate limits)
- Real-time monitoring only for premium alert triggers on high-value markets

### Core Components
- **Pattern Detection Engine**: Volume analysis, price movement, arbitrage detection, sentiment analysis
- **Scoring System**: Confidence score, profit potential, time sensitivity, risk assessment (all 0-100 or 1-5 scales)
- **Alert System**: Tier-based thresholds, multi-channel delivery (email, SMS, push, webhooks)

### Subscription Tiers
- Basic ($9.99): Daily digest, top 5 opportunities, email notifications
- Premium ($19.99): Real-time alerts, custom parameters, SMS, Discord/Slack
- Pro ($29.99): Custom analysis, advanced patterns, API access, priority support

## Tech Stack

- **Backend**: Python + FastAPI
- **Database**: PostgreSQL + Redis
- **Background Jobs**: APScheduler
- **HTTP Client**: httpx (async)

## Development Commands

```bash
# Start database services
docker-compose up -d

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Trigger manual data collection
curl -X POST http://localhost:8000/api/v1/collect
```

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # Settings from environment
├── api/routes/          # API endpoints
├── core/database.py     # PostgreSQL + Redis setup
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
└── services/
    ├── kalshi_client.py      # Kalshi API client
    ├── polymarket_client.py  # Polymarket API client
    ├── data_collector.py     # Scheduled data collection
    ├── alerts.py             # Alert generation service
    └── patterns/             # Pattern detection engine
        ├── base.py           # Base classes and types
        ├── volume.py         # Volume pattern detector
        ├── price.py          # Price pattern detector
        ├── arbitrage.py      # Arbitrage detector
        ├── scoring.py        # Pattern scoring system
        └── engine.py         # Main detection engine
```

## API Endpoints

### Markets
- `GET /api/v1/markets` - List markets (with filters)
- `GET /api/v1/markets/{id}` - Market details with history
- `GET /api/v1/markets/stats/summary` - Platform stats

### Patterns
- `GET /api/v1/patterns` - List detected patterns
- `GET /api/v1/patterns/opportunities` - Top opportunities by tier
- `GET /api/v1/patterns/stats` - Pattern statistics
- `GET /api/v1/patterns/types` - Available pattern types
- `POST /api/v1/patterns/analyze` - Trigger pattern analysis

### Alerts
- `GET /api/v1/patterns/alerts` - Get alerts by tier
- `GET /api/v1/patterns/alerts/stats` - Alert statistics

### System
- `GET /health` - Health check
- `POST /api/v1/collect` - Trigger data collection + analysis

## Pattern Types

| Type | Category | Description |
|------|----------|-------------|
| volume_spike | Volume | >3x normal volume detected |
| unusual_flow | Volume | Unusual directional betting |
| volume_divergence | Volume | Volume up, price stable |
| rapid_price_change | Price | >10% price movement |
| trend_reversal | Price | Momentum shift detected |
| support_break | Price | Price breaks support level |
| resistance_break | Price | Price breaks resistance |
| cross_platform_arbitrage | Arbitrage | Price diff between platforms |
| related_market_arbitrage | Arbitrage | Mispricing in related markets |

## Development Notes

- Data collection runs automatically every 15 minutes
- Direct API clients (Kalshi/Polymarket) are fallbacks for MCP
- Redis caches current market prices (1 hour TTL)
- Keep 6-12 months of historical data for pattern detection
