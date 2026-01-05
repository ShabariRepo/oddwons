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

### Subscription Tiers (all with 7-day free trial)
- Basic ($9.99/mo): Daily digest, top 5 opportunities, email notifications
- Premium ($19.99/mo): Real-time alerts, custom parameters, SMS, Discord/Slack
- Pro ($29.99/mo): Custom analysis, advanced patterns, API access, priority support

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Database**: PostgreSQL + Redis
- **AI**: Groq (gpt-oss-20b-128k default)
- **Background Jobs**: Railway Cron (production) / APScheduler (local)
- **HTTP Client**: httpx (async)
- **Email**: SendGrid

## Development Commands

```bash
# Start database services
docker-compose up -d

# Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend setup (in separate terminal)
cd frontend
npm install
npm run dev  # Runs on port 3000

# Trigger manual data collection
curl -X POST http://localhost:8000/api/v1/collect
```

## Project Structure

```
app/                          # Python backend
├── main.py                   # FastAPI entry point
├── config.py                 # Environment settings
├── api/routes/
│   ├── markets.py            # Market endpoints
│   ├── patterns.py           # Pattern detection endpoints
│   ├── insights.py           # AI insights endpoints (tier-gated)
│   ├── auth.py               # Authentication endpoints
│   └── billing.py            # Stripe billing endpoints
├── core/database.py          # PostgreSQL + Redis
├── models/
│   ├── market.py             # Market models
│   ├── user.py               # User + subscription models
│   └── ai_insight.py         # AIInsight, ArbitrageOpportunity, DailyDigest
├── schemas/
│   ├── market.py             # Market schemas
│   └── user.py               # User + auth schemas
└── services/
    ├── ai_agent.py           # Groq-powered MarketAnalysisAgent
    ├── kalshi_client.py
    ├── polymarket_client.py
    ├── data_collector.py
    ├── alerts.py
    ├── auth.py               # JWT authentication
    ├── billing.py            # Stripe integration
    └── patterns/             # Pattern detection engine

collect_data.py               # Railway cron: data collection (runs every 15 min)
run_analysis.py               # Railway cron: AI analysis (runs offset)

frontend/                     # Next.js frontend
├── src/
│   ├── app/
│   │   ├── (app)/            # Protected routes (require auth)
│   │   │   ├── page.tsx      # Dashboard
│   │   │   ├── opportunities/
│   │   │   ├── markets/
│   │   │   ├── alerts/
│   │   │   ├── analytics/
│   │   │   └── settings/     # Subscription management
│   │   ├── login/            # Public login page
│   │   └── register/         # Public registration page
│   ├── components/
│   │   ├── AuthProvider.tsx  # Auth context
│   │   ├── AppLayout.tsx     # Protected layout wrapper
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── hooks/useAPI.ts       # SWR data fetching hooks
│   └── lib/
│       ├── types.ts
│       └── auth.ts           # Auth utilities + billing API
└── package.json
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

### AI Insights (Tier-Gated)
- `GET /api/v1/insights/ai` - Get AI-powered recommendations (FREE: none, BASIC: top 5, PREMIUM: all+arbitrage, PRO: everything)
- `GET /api/v1/insights/arbitrage` - Cross-platform arbitrage opportunities (Premium+)
- `GET /api/v1/insights/digest` - Daily market digest (Basic+)
- `GET /api/v1/insights/stats` - Insight statistics
- `POST /api/v1/insights/refresh` - Trigger manual AI analysis (Pro only)

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login, returns JWT token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/change-password` - Change password

### Billing (Stripe)
- `GET /api/v1/billing/subscription` - Get current subscription
- `POST /api/v1/billing/checkout` - Create Stripe checkout session
- `POST /api/v1/billing/portal` - Create Stripe billing portal session
- `POST /api/v1/billing/webhook` - Stripe webhook handler
- `GET /api/v1/billing/prices` - Get available subscription prices

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

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/oddwons
REDIS_URL=redis://localhost:6379

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# AI Analysis (Groq)
GROQ_API_KEY=gsk_...
AI_ANALYSIS_ENABLED=true
AI_MODEL=gpt-oss-20b-128k

# Stripe Billing
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PREMIUM=price_...
STRIPE_PRICE_PRO=price_...

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxx
FROM_EMAIL=alerts@oddwons.ai
```

## Development Notes

- Data collection runs automatically every 15 minutes
- Direct API clients (Kalshi/Polymarket) are fallbacks for MCP
- Redis caches current market prices (1 hour TTL)
- Keep 6-12 months of historical data for pattern detection
- JWT tokens are stored in localStorage on frontend
- Protected routes redirect to /login if not authenticated

## Recent Updates (Jan 2026)

### Data Collection Improvements
- **Rate Limiting**: 0.5s delay for Kalshi, 0.2s for Polymarket to avoid 429 errors
- **Page Limits**: Max 50 pages Kalshi (~5000 markets), 100 pages Polymarket (~25000 markets)
- **Retry Logic**: Auto-retry on rate limit errors with 5s backoff
- **Timezone Fix**: All datetime fields converted to naive UTC for PostgreSQL compatibility
- **Polymarket Parsing Fix**: JSON string fields (`outcomes`, `outcomePrices`) now parsed correctly

### AI Analysis Improvements
- **Category-Based Analysis**: Markets grouped by category (politics, sports, crypto, finance, tech, etc.) for focused AI context
- **Batch Processing**: Separate Groq calls per category instead of one massive prompt
- **Better Insights**: Cross-market correlation detection within categories
- **Category Inference**: Automatic category detection from market titles using keyword matching

### Current Data Volume
- Kalshi: ~5,000 active markets
- Polymarket: ~25,000 active markets
- Total: ~30,000 markets per collection cycle
