# OddWons - Current Status & Quick Reference

## Production URLs
- **App:** https://oddwons.ai
- **X/Twitter:** https://x.com/oddwons (automated posting active)

---

## Worker Service Schedule (Railway)

### Data Pipeline (Every 15 min)
- Data collection from Kalshi + Polymarket (~1-2 min)
- AI analysis with Groq (~1-2 min)
- Cross-platform market matching (~30-60s)
- Alert email processing

### X (Twitter) Posting (~19 posts/day)

| Time (EST) | Post Type |
|------------|-----------|
| 8 AM | Morning Movers |
| 9 AM | Crypto Spotlight |
| 10 AM | Platform Gap |
| 11 AM | Politics Spotlight |
| 12 PM | Market Highlight |
| 1 PM | Sports Spotlight |
| 2 PM | Platform Gap |
| 3 PM | Daily Poll |
| 4 PM | Big Movers |
| 5 PM | Finance Spotlight |
| 6 PM | Market Highlight |
| 7 PM | Promo (with logo) |
| 8 PM | Platform Gap |
| 9 PM | Entertainment Spotlight |
| 10 PM | Market Highlight |
| 11 PM | Late Night Sports |
| 12 AM | Late Night Crypto |
| 1 AM | Late Night Action |
| Sunday 10 AM | Weekly Recap Thread |

### Email Jobs
- 8 AM UTC: Daily digest emails
- 10 AM UTC: Trial reminder emails
- Every 5 min: Process pending alert emails

### Maintenance
- 3 AM UTC: Database cleanup (7-day snapshot retention)

---

## Database Cleanup

**Automated:** Runs daily at 3 AM UTC via worker.py

**Manual cleanup (if needed):**
```sql
-- Check table sizes
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Delete old snapshots (7 day retention)
DELETE FROM market_snapshots
WHERE timestamp < NOW() - INTERVAL '7 days';

-- Reclaim disk space
VACUUM FULL market_snapshots;
```

---

## Tier Value Matrix

| Feature | FREE | BASIC | PREMIUM | PRO |
|---------|------|-------|---------|-----|
| **Data freshness** | 24h+ old | 6h+ old | 1h+ old | Real-time |
| **# of insights** | 3 | 10 | 30 | 50 |
| **Volume/movement** | - | Yes | Yes | Yes |
| **Movement context** | - | - | Yes | Yes |
| **Upcoming catalyst** | - | - | Yes | Yes |
| **Source articles** | - | - | Yes | Yes |
| **Analyst note** | - | - | - | Yes |
| **Daily digest email** | - | Yes | Yes | Yes |
| **Cross-platform gaps** | - | - | Yes | Yes |

---

## Environment Variables

### Required for X Bot
```env
X_CONSUMER_KEY=jWYlfYS...       # API Key from X Developer Portal
X_CONSUMER_SECRET=2ttLQgT...    # API Key Secret
X_API_KEY=2010413698...         # Access Token (with Read+Write)
X_API_SECRET=ofL6mEsG...        # Access Token Secret
```

### AI Services
```env
GROQ_API_KEY=gsk_...            # For tweet generation + insights
GEMINI_API_KEY=AIzaSy...        # For web search grounding
```

---

## Quick Test Commands

```bash
# Test X connection
python -c "
import asyncio
from app.services.x_poster import test_x_connection
asyncio.run(test_x_connection())
"

# Trigger manual X post
python -c "
import asyncio
from app.services.x_poster import run_scheduled_posts
asyncio.run(run_scheduled_posts('morning'))
"

# Run full data pipeline manually
python -c "
import asyncio
from worker import run_full_pipeline
asyncio.run(run_full_pipeline())
"
```

---

## Analytics
- **Google Ads:** AW-17868225226 (tracking + audiences)
- **Microsoft Clarity:** uzztv414sk (session recordings + heatmaps)

---

## Recent Changes (Jan 2026)

1. **X Bot Upgrade:** Hourly posting (8AM-1AM EST), category spotlights, polls, late night strategy
2. **Scheduler Fix:** Scheduler starts before pipeline to prevent delayed X posts
3. **Analytics:** Added Google Ads tag + Microsoft Clarity
4. **All tweets include #OddWons hashtag**
