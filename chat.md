# OddWons - Production Status

_Last updated: January 7, 2026_

---

## Current Status: DEPLOYED

### Live URLs
- **Frontend**: https://oddwons.ai
- **Backend API**: https://api.oddwons.ai

### Services Status
- Backend: Running (health check passing)
- Frontend: Running (Next.js serving pages)
- PostgreSQL: Connected via Railway internal network
- Redis: Connected via Railway internal network

---

## Environment Variables Configured

### Shared Variables (all services)
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `SECRET_KEY` - JWT signing key
- `ALGORITHM` - HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES` - 10080 (7 days)
- `DEBUG` - false
- `LOG_LEVEL` - INFO
- `COLLECTION_INTERVAL_MINUTES` - 15
- `FRONTEND_URL` - https://oddwons.ai
- `FROM_EMAIL` - alerts@oddwons.ai
- `STRIPE_SECRET_KEY` - Live key configured
- `STRIPE_PUBLISHABLE_KEY` - Live key configured

### Backend-Specific
- `STRIPE_WEBHOOK_SECRET` - For Stripe event verification

### Frontend-Specific
- `BACKEND_URL` - https://api.oddwons.ai (for Next.js rewrites)

---

## DNS Configuration

Connected to Cloudflare:
- `oddwons.ai` -> Railway frontend service
- `api.oddwons.ai` -> Railway backend service

---

## Recent Fixes

1. **Stats Endpoint Fix** (Jan 7)
   - `/api/v1/markets/stats/summary` was failing with Redis errors
   - Fixed to handle Redis gracefully (non-blocking)

2. **Frontend Proxy** (Jan 7)
   - Added `BACKEND_URL` env var for Next.js rewrites
   - API calls proxied through frontend to backend

---

## Next Steps (Production Readiness)

- [ ] Run data collection to populate markets
- [ ] Run AI analysis to generate insights
- [ ] Test Stripe checkout flow with real payments
- [ ] Verify Stripe webhook receives events
- [ ] Monitor error logs for any issues
- [ ] Set up SendGrid for email alerts

---

## Commands

```bash
# Trigger data collection
curl -X POST https://api.oddwons.ai/api/v1/collect

# Check backend health
curl https://api.oddwons.ai/health

# Check markets
curl "https://api.oddwons.ai/api/v1/markets?limit=5"

# Check stats
curl https://api.oddwons.ai/api/v1/markets/stats/summary
```
