# OddWons

AI-powered prediction market analysis for Kalshi and Polymarket.

## Features

- Real-time market data from Kalshi and Polymarket
- Pattern detection (volume spikes, price movements, arbitrage)
- Subscription tiers with Stripe billing
- Email alerts for opportunities

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Auth**: JWT tokens
- **Payments**: Stripe

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

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API docs.

## License

MIT
