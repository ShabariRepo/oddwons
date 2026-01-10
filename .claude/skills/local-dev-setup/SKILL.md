# Local Development Setup

> **When to use this skill:** When setting up the local development environment, debugging Stripe webhooks, testing subscription flows, or helping a new developer get started.

## Quick Start (4 Terminals)

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `docker compose up` | Postgres + Redis |
| 2 | `./scripts/stripe-webhook.sh` | Stripe webhook forwarding |
| 3 | `cd backend && uvicorn app.main:app --reload` | FastAPI backend |
| 4 | `cd frontend && npm run dev` | Next.js frontend |

---

## Prerequisites

```bash
# macOS
brew install docker stripe/stripe-cli/stripe python@3.11 node@20

# Login to Stripe (one time)
stripe login
```

---

## Environment Setup

### 1. Clone and Setup

```bash
git clone <repo>
cd oddwons

# Python backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node frontend
cd frontend
npm install
cd ..
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Database (Docker)
DATABASE_URL=postgresql+asyncpg://oddwons:oddwons_dev@localhost:5432/oddwons
REDIS_URL=redis://localhost:6379

# Authentication
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Stripe (TEST MODE - get from Stripe Dashboard > Developers > API Keys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...  # From stripe listen command
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PREMIUM=price_...
STRIPE_PRICE_PRO=price_...

# SendGrid (optional for local - emails will send to real addresses!)
SENDGRID_API_KEY=
FROM_EMAIL=alerts@oddwons.ai

# AI Analysis
GROQ_API_KEY=gsk_...
AI_ANALYSIS_ENABLED=true
AI_MODEL=openai/gpt-oss-20b

# Gemini
GEMINI_API_KEY=...
```

---

## Stripe CLI Setup (Critical for Testing Subscriptions)

### Why It's Needed

Production has a webhook at `https://oddwons.ai/api/v1/billing/webhook` that receives Stripe events. Locally, Stripe can't reach `localhost`, so the CLI forwards events.

### One-Time Setup

```bash
# 1. Login to Stripe (opens browser)
stripe login

# 2. Start the listener (note the whsec_... it displays)
stripe listen --forward-to localhost:8000/api/v1/billing/webhook

# Output:
# > Ready! Your webhook signing secret is whsec_12345abcdef...

# 3. Add to .env
STRIPE_WEBHOOK_SECRET=whsec_12345abcdef...

# 4. Restart backend to pick up new env var
```

### The whsec_ Secret

- **Stays the same** between `stripe listen` runs (tied to your CLI login)
- **Changes if** you `stripe logout` and login again
- **Only update .env** if it changes

### Running Daily

```bash
# Just run this - same whsec_ as before
stripe listen --forward-to localhost:8000/api/v1/billing/webhook

# Or use the script
./scripts/stripe-webhook.sh
```

### Convenience Script

```bash
# scripts/stripe-webhook.sh
#!/bin/bash
echo "Starting Stripe webhook forwarder..."
echo "Keep this terminal open while testing!"
echo ""
stripe listen \
  --forward-to localhost:8000/api/v1/billing/webhook \
  --events checkout.session.completed,customer.subscription.created,customer.subscription.deleted,customer.subscription.updated,invoice.paid,invoice.payment_failed
```

### Testing Webhooks

```bash
# Trigger test events
stripe trigger customer.subscription.created
stripe trigger customer.subscription.updated
stripe trigger invoice.payment_failed

# You should see in backend logs:
# INFO: Received Stripe webhook: customer.subscription.created
```

---

## Database Setup

### Start Docker

```bash
docker compose up -d
```

This starts:
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

### Run Migrations

```bash
# Create tables
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Or use alembic if configured
alembic upgrade head
```

### Reset Database

```bash
# Stop containers and remove volumes
docker compose down -v

# Start fresh
docker compose up -d
```

### Connect to Database

```bash
# psql
docker exec -it oddwons-postgres psql -U oddwons -d oddwons

# Or use pgAdmin/DBeaver with:
# Host: localhost
# Port: 5432
# User: oddwons
# Password: oddwons_dev
# Database: oddwons
```

---

## Testing Subscription Flows

### Full Trial Flow Test

1. **Start all 4 terminals** (Docker, Stripe CLI, Backend, Frontend)

2. **Create a test user** via the app or API

3. **Go through checkout:**
   - Navigate to `/pricing`
   - Select a plan
   - Use Stripe test card: `4242 4242 4242 4242`
   - Any future expiry, any CVC

4. **Watch the Stripe CLI terminal:**
   ```
   --> customer.subscription.created
   <-- 200 OK
   ```

5. **Verify in database:**
   ```sql
   SELECT email, subscription_status, subscription_tier, trial_end 
   FROM users WHERE email = 'test@example.com';
   ```

### Test Cards

| Card Number | Result |
|-------------|--------|
| `4242 4242 4242 4242` | Success |
| `4000 0000 0000 0341` | Attach fails |
| `4000 0000 0000 9995` | Payment fails |
| `4000 0027 6000 3184` | 3D Secure required |

### Manual Status Updates (Quick Testing)

```sql
-- Set user to trialing (full PRO access)
UPDATE users 
SET subscription_status = 'trialing', subscription_tier = 'BASIC', trial_end = NOW() + INTERVAL '7 days'
WHERE email = 'test@example.com';

-- Set user to active paid
UPDATE users 
SET subscription_status = 'active', subscription_tier = 'PREMIUM'
WHERE email = 'test@example.com';

-- Set user to free (expired)
UPDATE users 
SET subscription_status = 'inactive', subscription_tier = 'FREE'
WHERE email = 'test@example.com';
```

---

## Common Issues

### "Stripe webhook secret not configured"

```bash
# Check .env has the secret
grep STRIPE_WEBHOOK_SECRET .env

# Should show: STRIPE_WEBHOOK_SECRET=whsec_...
# If empty, run stripe listen and copy the secret
```

### "Invalid signature" on webhooks

```bash
# The whsec_ in .env doesn't match the running stripe listen session
# Solution: Copy the whsec_ from the current stripe listen output to .env
# Then restart the backend
```

### Webhook events not reaching backend

1. Is `stripe listen` running? (Check terminal 2)
2. Is backend running? (Check terminal 3)
3. Is the URL correct? (`localhost:8000/api/v1/billing/webhook`)

### Database connection refused

```bash
# Check Docker is running
docker ps

# Should show oddwons-postgres and oddwons-redis
# If not:
docker compose up -d
```

### Frontend can't reach backend (CORS)

Backend should have:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Stripe Dashboard Links (Test Mode)

- [API Keys](https://dashboard.stripe.com/test/apikeys)
- [Products & Prices](https://dashboard.stripe.com/test/products)
- [Customers](https://dashboard.stripe.com/test/customers)
- [Subscriptions](https://dashboard.stripe.com/test/subscriptions)
- [Webhook Logs](https://dashboard.stripe.com/test/webhooks)
- [Events](https://dashboard.stripe.com/test/events)

---

## Matching Production

| Aspect | Local | Production |
|--------|-------|------------|
| API | `http://localhost:8000` | `https://oddwons.ai` |
| Frontend | `http://localhost:3000` | `https://oddwons.ai` |
| Stripe Mode | Test (`sk_test_`) | Live (`sk_live_`) |
| Webhook | `stripe listen` → localhost | Direct to `oddwons.ai/api/v1/billing/webhook` |
| Database | Docker Postgres | Railway Postgres |
| Redis | Docker Redis | Railway Redis |

Local dev mimics production exactly - same webhook handlers, same code paths, just different credentials.

---

## Useful Commands

```bash
# Logs
docker compose logs -f postgres
docker compose logs -f redis

# Database shell
docker exec -it oddwons-postgres psql -U oddwons -d oddwons

# Redis CLI
docker exec -it oddwons-redis redis-cli

# Run data collection manually
curl -X POST http://localhost:8000/api/v1/collect

# Check API health
curl http://localhost:8000/health

# Trigger Stripe events
stripe trigger customer.subscription.created
stripe trigger checkout.session.completed
```
