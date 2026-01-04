# OddWons

AI-powered prediction market analysis for Kalshi and Polymarket. Get actionable insights, not just data.

## Features

- **AI-Powered Analysis** - Groq LLM integration for intelligent market recommendations
- **Real-time Market Data** - Direct API integration with Kalshi and Polymarket
- **Actionable Insights** - "STRONG_BET: Trump Iowa at 62¢ is mispriced" not just "volume spike detected"
- **Cross-Platform Arbitrage** - Finds opportunities with >2% edge
- **Daily Digests** - AI-generated market summaries by subscription tier
- **Pattern Detection** - Volume spikes, price movements, momentum shifts
- **Tier-Gated Access** - FREE/BASIC/PREMIUM/PRO with increasing insight depth
- **Stripe Billing** - Subscription management
- **Email Alerts** - SendGrid integration for opportunity notifications

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **AI**: Groq (gpt-oss-20b-128k default)
- **Auth**: JWT tokens
- **Payments**: Stripe
- **Email**: SendGrid

## Local Development

```bash
# Start database services
brew services start postgresql@14
brew services start redis

# Create database
createdb oddwons

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your settings
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Deploy to Railway

### One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/oddwons)

### Manual Setup

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. Create project and provision services:
   ```bash
   railway init

   # Add PostgreSQL
   railway add --plugin postgresql

   # Add Redis
   railway add --plugin redis
   ```

3. Deploy backend:
   ```bash
   railway up
   ```

4. Deploy frontend:
   ```bash
   cd frontend
   railway up
   ```

5. Set environment variables in Railway dashboard:
   ```
   SECRET_KEY=<generate-secure-key>
   STRIPE_SECRET_KEY=sk_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PRICE_BASIC=price_...
   STRIPE_PRICE_PREMIUM=price_...
   STRIPE_PRICE_PRO=price_...
   ```

6. For frontend, set:
   ```
   BACKEND_URL=https://<your-backend>.railway.app
   ```

## Subscription Tiers

| Tier | Price | Features |
|------|-------|----------|
| **FREE** | $0 | Market data browsing, upgrade prompts |
| **BASIC** | $9/mo | Top 5 AI picks daily, high confidence only |
| **PREMIUM** | $29/mo | All insights + arbitrage, hourly refresh, full reasoning |
| **PRO** | $99/mo | Everything + edge explanations, real-time alerts, manual refresh |

## AI Insights API

```bash
# Get AI insights (tier-gated)
GET /api/v1/insights/ai

# Get arbitrage opportunities (Premium+)
GET /api/v1/insights/arbitrage

# Get daily digest (Basic+)
GET /api/v1/insights/digest

# Trigger manual analysis (Pro only)
POST /api/v1/insights/refresh
```

## Railway Deployment (Production)

The app uses separate cron jobs for production:

- **api-server** - Main FastAPI app
- **data-collector** - Runs every 15 min, collects market data
- **ai-analyzer** - Runs offset from collector, performs AI analysis
- **postgres** - PostgreSQL database
- **redis** - Redis cache

See `CLAUDE_CODE_INSTRUCTIONS.md` for detailed Railway setup.

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API docs.

## License

MIT
