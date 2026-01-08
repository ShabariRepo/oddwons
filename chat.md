# OddWons - Production Status

_Last updated: January 7, 2026_

---

## Current Status: DEPLOYED AND WORKING

### Live URLs
- **Frontend**: https://oddwons.ai
- **Backend API**: https://api.oddwons.ai

### Database Stats
- 801 Kalshi markets
- 1,533 Polymarket markets
- $2.2 Billion total volume
- Automatic collection every 15 minutes via scheduler

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
- `BACKEND_URL` - https://api.oddwons.ai (for Next.js rewrites, set at build time)

---

## DNS Configuration

Connected to Cloudflare:
- `oddwons.ai` -> Railway frontend service
- `api.oddwons.ai` -> Railway backend service

---

## Issues Fixed During Deployment

1. **Stats Endpoint Fix** - Made Redis optional (graceful fallback)
2. **Frontend API Proxy** - Set `BACKEND_URL` at Docker build time
3. **Database Tables** - Fixed model imports in `init_db()`
4. **Data Collection** - Debug endpoints helped identify timeout issues

---

## Debug Endpoints (can be removed later)

- `GET /debug/db` - Check database tables
- `GET /debug/apis` - Test API client connectivity
- `POST /debug/test-collect` - Run small collection batch

---

## Commands

```bash
# Check backend health
curl https://api.oddwons.ai/health

# Check stats
curl https://api.oddwons.ai/api/v1/markets/stats/summary

# Check markets
curl "https://api.oddwons.ai/api/v1/markets?limit=5"

# Test collection (via debug endpoint)
curl -X POST https://api.oddwons.ai/debug/test-collect
```

---

## Next Steps

- [ ] Run AI analysis to generate insights (`run_analysis.py`)
- [ ] Test Stripe checkout flow with real payments
- [ ] Verify Stripe webhook receives events
- [ ] Set up SendGrid for email alerts
- [ ] Remove debug endpoints once stable
