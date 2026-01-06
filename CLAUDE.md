# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OddWons is a subscription-based **research companion** for prediction market enthusiasts. We inform and contextualize prediction markets using AI - think Bloomberg Terminal for prediction markets, NOT a tipster.

**CRITICAL PRODUCT PHILOSOPHY:**
- We INFORM and CONTEXTUALIZE, not recommend bets
- We NEVER use words like "BET", "EDGE", "ALPHA", "STRONG_BET"
- We focus on WHAT'S HAPPENING, not what to bet on
- We ALWAYS return results (never 0 highlights)

Users pay for:
- Curated market summaries
- Context on price movements
- Time savings (we do the research)
- Cross-platform visibility
- Alerts when markets move
- Understanding what odds imply

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
- **Free**: Preview (top 3 highlights, summaries only)
- **Basic ($9.99/mo)**: Top highlights with context, daily briefings
- **Premium ($19.99/mo)**: All highlights + movement analysis + upcoming catalysts
- **Pro ($29.99/mo)**: Full analyst notes + price gap analysis + real-time updates

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Database**: PostgreSQL + Redis
- **AI**: Groq (openai/gpt-oss-20b default)
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
│   ├── cross_platform.py     # Cross-platform spotlight endpoints
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
    ├── kalshi_client.py      # Kalshi API (events + markets endpoints)
    ├── polymarket_client.py  # Polymarket API (gamma + clob)
    ├── cross_platform.py     # Cross-platform matching and spotlight
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

### AI Insights (Tier-Gated) - COMPANION STYLE
- `GET /api/v1/insights/ai` - Get market highlights (FREE: 3 preview, BASIC: 10 with context, PREMIUM: 30+catalysts, PRO: all+analyst notes)
- `GET /api/v1/insights/arbitrage` - Cross-platform price gap analysis (Premium+)
- `GET /api/v1/insights/digest` - Daily market briefing (Basic+)
- `GET /api/v1/insights/stats` - Highlight statistics by category
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
- `POST /api/v1/billing/sync` - Sync subscription status from Stripe (manual refresh)
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
AI_MODEL=openai/gpt-oss-20b

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
- Kalshi: ~35,000 markets (many zero-volume prop bets)
- Polymarket: ~35,000 open markets (using `closed=false` API param)
- Total: ~95,000 markets in database
- Meaningful markets (volume >$1k): ~6,600

### Polymarket Collection Fix (Jan 2026)
- Changed API param from `active=true` to `closed=false`
- The `active` param means "not archived", NOT "open for trading"
- Now correctly fetches all tradeable markets
- Added volume_24h (from event's `volume24hr`)
- Added spread, best_ask to snapshots

### Computed Fields on Markets API
Every market response now includes (computed at query time):
- `implied_probability`: yes_price as percentage (0-100)
- `price_change_24h`: change vs 24h ago snapshot
- `price_change_7d`: change vs 7d ago snapshot
- `volume_rank`: percentile (0-100) within category
- `spread`: bid-ask spread if available
- `has_ai_highlight`: boolean flag if AI insight exists

### Companion Approach (Jan 2026)
Major product shift from "alpha hunter" to "research companion":

**Database Schema Changes:**
- `AIInsight` model now stores: summary, current_odds, implied_probability, volume_note, recent_movement, movement_context, upcoming_catalyst, analyst_note, interest_score
- `DailyDigest` model now stores: headline, top_movers, most_active, upcoming_catalysts, category_snapshots, notable_price_gaps

**AI Prompts:**
- `CATEGORY_CONTEXT` dict provides domain knowledge per category (politics, sports, crypto, finance, tech, entertainment, weather, world)
- Prompts instruct AI to ALWAYS return 3-5+ highlights per category
- No betting advice language allowed in responses

**API Response Changes:**
- Free tier now gets 3 preview highlights (was blocked)
- All tiers get progressively more context instead of more "betting tips"
- Stats endpoint shows highlights_by_category instead of strong_bets_24h

### Cross-Platform Spotlight Feature (Jan 2026)
**KEY VALUE PROP:** Show users when the same event is priced differently on Kalshi vs Polymarket.

**New API Endpoints:**
- `GET /api/v1/cross-platform/matches` - List all matched markets (public)
- `GET /api/v1/cross-platform/spotlight/{match_id}` - Rich spotlight with full context (auth required)
- `GET /api/v1/cross-platform/spotlights` - Top N spotlights by volume (auth required)
- `GET /api/v1/cross-platform/watch` - Daily digest section (Premium+ in digest)
- `GET /api/v1/cross-platform/stats` - Match statistics (public)

**CrossPlatformSpotlight Response Contains:**
```json
{
  "match_id": "fed-chair-warsh",
  "topic": "Trump nominates Kevin Warsh as Fed Chair",
  "category": "Politics",
  "kalshi": {"market_id": "...", "yes_price": 41.0, "volume": 3291774},
  "polymarket": {"market_id": "...", "yes_price": 38.5, "volume": 3575507},
  "price_gap_cents": 2.5,
  "gap_direction": "kalshi_higher",
  "news_headlines": [
    {"title": "WSJ: Warsh met with Trump transition team", "date": "Jan 3"},
    {"title": "Bessent reportedly favors Warsh for Fed Chair", "date": "Jan 2"}
  ],
  "kalshi_history": {"current_price": 41.0, "price_7d_ago": 35.0, "trend": "up"},
  "polymarket_history": {"current_price": 38.5, "price_7d_ago": 32.0, "trend": "up"},
  "key_dates": [
    {"date": "Jan 20, 2025", "description": "Inauguration Day"},
    {"date": "Late Jan 2025", "description": "Expected Fed Chair announcement"}
  ],
  "ai_analysis": "3-4 sentences explaining the market...",
  "gap_explanation": "Why the gap might exist...",
  "related_markets": [...],
  "combined_volume": 6867281
}
```

**Matching Patterns (25+):**
- Fed Chair nominations: Warsh, Hassett, Waller, Shelton
- 2028 Democratic nominees: Newsom, Shapiro, Buttigieg, Whitmer
- Cabinet confirmations: Hegseth, Bondi, Patel
- Economic indicators: recession, inflation, fed rate
- Crypto: Bitcoin/Ethereum price targets
- Policy: TikTok, tariffs
- Sports: Super Bowl outcomes

**Files:**
- `app/services/cross_platform.py` - CrossPlatformService class
- `app/api/routes/cross_platform.py` - API endpoints
- `app/schemas/market.py` - CrossPlatformSpotlight schema

### Kalshi Events Endpoint Fix (Jan 2026)
- `/markets` endpoint returns sports parlays only
- `/events` endpoint returns political/economic prediction markets
- Now fetch from BOTH endpoints to get comprehensive coverage
- Prices in cents (0-100) converted to decimal (0-1) to match Polymarket
- Result: 6,786 Kalshi markets with volume > $1k (was 360)

### Pattern Analysis Scope Expansion (Jan 2026)
- Changed from limit=500 to analyzing ALL markets with volume > $1k
- Now covers ~6,600 meaningful markets instead of top 500
- min_volume parameter added to load_market_data()

### AI Content Generation for Spotlights (Jan 2026)
- News headlines now AI-generated via Groq (not templates)
- AI analysis includes: summary, gap explanation, momentum summary, key risks
- Price history passed to AI for momentum context
- Fallback methods available when Groq is unavailable
- IMPORTANT: Server must load GROQ_API_KEY from .env (`set -a && source .env && set +a`)

### Dynamic Cross-Platform Matching (Jan 2026)
**MAJOR IMPROVEMENT:** From 6 hardcoded patterns to 420+ dynamic matches!

**New Components:**
- `cross_platform_matches` table: Stores discovered matches with cached prices/volumes
- `CrossPlatformMatch` model: SQLAlchemy model in `app/models/cross_platform_match.py`
- `MarketMatcher` service: Uses rapidfuzz for fuzzy title matching (`app/services/market_matcher.py`)
- Integrated into `run_analysis.py` to discover matches every 15 minutes

**How It Works:**
1. MarketMatcher loads all Kalshi and Polymarket markets with volume > $1k
2. Uses fuzzy string matching (token_sort_ratio) with 70% similarity threshold
3. Validates matches by checking close dates within 365 days
4. Saves matches to database with prices, volumes, similarity scores
5. CrossPlatformService reads from DB instead of hardcoded patterns

**Database Schema:**
```sql
cross_platform_matches (
  match_id VARCHAR(255) UNIQUE,
  topic VARCHAR(500),
  category VARCHAR(100),
  kalshi_market_id, kalshi_title, kalshi_yes_price, kalshi_volume,
  polymarket_market_id, polymarket_title, polymarket_yes_price, polymarket_volume,
  price_gap_cents, gap_direction, combined_volume, similarity_score,
  ai_analysis, news_headlines, gap_explanation (cached AI content)
)
```

**Dependency:**
```bash
pip install rapidfuzz  # Added to requirements.txt
```

**Run Manually:**
```python
from app.services.market_matcher import run_market_matching
result = await run_market_matching(min_volume=1000)
print(f"Found {result['matches_found']} matches")
```

### Frontend Wiring to Real Data (Jan 2026)
**MAJOR UPDATE:** Frontend now shows real data from backend instead of boilerplate.

**Dashboard (`/dashboard`):**
- AI Market Highlights section showing Groq-powered insights
- Cross-Platform Watch showing price comparisons between Kalshi/Polymarket
- Stats cards for: Markets Tracked, AI Highlights, Total Volume, Cross-Platform Matches

**AI Highlights page (`/opportunities`):**
- Shows real AI insights from `ai_insights` table (167+ active)
- Category filtering (politics, sports, crypto, finance, tech, entertainment)
- Tier-gated content (FREE: summary, BASIC: +volume/movement, PREMIUM: +catalyst, PRO: +analyst notes)

**Cross-Platform page (`/cross-platform`):**
- Lists all 420+ fuzzy-matched markets between Kalshi and Polymarket
- Shows price gaps, volumes, match confidence scores
- Filter by minimum gap size (1¢, 2¢, 3¢, 5¢, 10¢)

**New Frontend Files:**
- `frontend/src/app/(app)/cross-platform/page.tsx` - Cross-platform comparison page
- `frontend/src/lib/types.ts` - Added AIInsight, CrossPlatformMatch, DailyDigest types
- `frontend/src/lib/api.ts` - Added getAIInsights, getCrossPlatformMatches, etc.
- `frontend/src/hooks/useAPI.ts` - Added useAIInsights, useCrossPlatformMatches hooks

**Sidebar Navigation:**
- Dashboard -> AI Highlights -> Cross-Platform -> Markets -> Alerts -> Analytics -> Settings

### Gemini Web Search + Bro Vibes Pipeline (Jan 2026)
**MAJOR IMPROVEMENT:** AI insights now backed by REAL NEWS from Google Search.

**Architecture:**
```
Market data → Gemini web search → real headlines
     ↓
Market data + real news → Groq → informed analysis with bro vibes
```

**Cost:** FREE (Gemini: 1,500 searches/day, Groq: ~$0.02/run)

**New Components:**
- `app/services/gemini_search.py` - Gemini 2.0 Flash with Google Search grounding
- Updated `app/services/ai_agent.py` - Accepts news_context, uses "bro vibes" tone
- Updated `app/services/patterns/engine.py` - Fetches news for each category before analysis

**Environment:**
```bash
GEMINI_API_KEY=AIzaSy...  # Add to .env
```

**Bro Vibes Tone Examples:**
- Instead of: "Market shows elevated probability due to recent polling"
- Now: "Yo this market is heating up - recent polls got it jumping to 62%, no cap"

- Instead of: "Significant price movement following news event"
- Now: "Bro this thing moved HARD after the news dropped - we're talking +12% in like 2 hours"

**Dependency:**
```bash
pip install google-genai  # Added to requirements.txt
```

### Performance Fix: O(n²) Arbitrage Detection (Jan 2026)
Fixed arbitrage detector that was hanging for 25+ minutes due to 16M+ string comparisons.
- Limited arbitrage detection to top 500 markets by volume per platform
- Full cross-platform matching handled by MarketMatcher service (uses faster rapidfuzz)
- Analysis now runs in ~90 seconds

### Clickable Detail Pages & Source Articles (Jan 2026)
**MAJOR UI/UX IMPROVEMENT:** All cards are now clickable with rich detail pages!

**New Frontend Pages:**
- `frontend/src/app/(app)/insights/[id]/page.tsx` - AI insight detail page
- `frontend/src/app/(app)/markets/[id]/page.tsx` - Market detail page with AI insight + cross-platform

**New/Enhanced API Endpoints:**
- `GET /api/v1/insights/ai/{id}` - Full insight detail with source articles
- `GET /api/v1/markets/{market_id}` - Enhanced to include AI insight + cross-platform match

**Source Articles Feature (THE HOMEWORK):**
- `source_articles` and `news_context` columns added to `ai_insights` table
- Gemini web search results stored with each insight
- Displays sources on insight detail page (Premium+ tiers)
- Shows title, source name, date, and relevance

**Insight Detail Page Shows:**
- Full AI summary with bro vibes
- Current odds (Yes/No percentages)
- Price history chart
- Movement context (why it moved)
- Upcoming catalyst (key dates)
- Source articles (our homework - Gemini search results)
- Cross-platform pricing comparison
- Direct links to trade on Kalshi/Polymarket

**Market Detail Page Shows:**
- Market title, platform, status
- Current prices + 24h/7d changes
- Volume stats + category rank
- Price history chart
- AI insight (if exists) with sources
- Cross-platform comparison
- External link to platform

**Clickable Navigation:**
- Dashboard insight cards → `/insights/{id}`
- Opportunities page cards → `/insights/{id}`
- Markets table rows → `/markets/{market_id}`
- Cross-platform cards → `/cross-platform`

**New Types Added:**
- `InsightDetailResponse` - Full insight with sources, market, price history
- `MarketDetailResponse` - Full market with AI insight, cross-platform
- `SourceArticle` - title, source, date, relevance

**New Hooks Added:**
- `useInsightDetail(id)` - Fetch single insight with all context
- `useMarketDetail(id)` - Fetch single market with AI + cross-platform
