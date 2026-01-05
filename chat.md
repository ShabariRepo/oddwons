# PRIORITY FIX: AI Highlights Not Showing

## The Problem

- Dashboard shows **167 AI Highlights** (from `/insights/stats`)
- AI Highlights page shows **0 highlights** (from `/insights/ai`)

## Root Cause

The `/insights/ai` endpoint has an aggressive filter that joins with the Markets table:

```python
# In app/api/routes/insights.py, line ~45
.join(Market, AIInsight.market_id == Market.id, isouter=True)
.where(
    (Market.id == None) |  # Allow if market not found
    (
        (Market.status == 'active') &
        (Market.yes_price > 0.02) &
        (Market.yes_price < 0.98)
    )
)
```

The AI insights have `market_id` values that either:
1. Don't exist in the `markets` table
2. Are now resolved/closed
3. Have prices at 0% or 100%

So ALL insights get filtered out.

## The Fix

**Option A: Remove the market join filter (quick fix)**

In `app/api/routes/insights.py`, change the query to NOT join with markets:

```python
# Build query - just get active insights
query = (
    select(AIInsight)
    .where(AIInsight.status == "active")
    .where(AIInsight.expires_at > datetime.utcnow())
)

if category:
    query = query.where(AIInsight.category == category)

query = query.order_by(
    AIInsight.interest_score.desc().nullslast(),
    AIInsight.created_at.desc()
).limit(tier_limit)
```

**Option B: Fix the join condition (better but more complex)**

Use a LEFT OUTER JOIN and allow insights even if market is missing:

```python
from sqlalchemy.orm import aliased

# Build query with proper outer join
query = (
    select(AIInsight)
    .outerjoin(Market, AIInsight.market_id == Market.id)
    .where(AIInsight.status == "active")
    .where(AIInsight.expires_at > datetime.utcnow())
    .where(
        # Include if: no matching market OR market is active with good price
        (Market.id.is_(None)) | 
        (
            (Market.status == 'active') &
            (Market.yes_price > 0.02) &
            (Market.yes_price < 0.98)
        )
    )
)
```

**Option C: Regenerate insights with valid market_ids**

Run `python run_analysis.py` to create fresh insights linked to current active markets.

---

## Secondary Issues

### Dashboard Cross-Platform Count Wrong
- Dashboard shows "4" cross-platform matches
- Cross-Platform page shows "390"
- Check: Dashboard calls `useCrossPlatformMatches({ limit: 4 })` but displays `crossPlatform?.total`
- The total should reflect ALL matches, not just the limited result

**Fix in dashboard:** The stats card should use a separate stats call:
```typescript
// Dashboard should use stats endpoint for the count
<StatsCard
  title="Cross-Platform"
  value={crossPlatformStats?.total_matches || crossPlatform?.total || 0}
  ...
/>
```

Or the API should return total regardless of limit (it already does, but frontend reads from limited result).

### Language Cleanup Needed
- Analytics page: "Avg Confidence" → "Avg Relevance Score"
- Analytics page: "Related Market Arb" → "Related Market Analysis"
- Run: `grep -rn 'Confidence\|Arb' frontend/src/`

---

## Commands to Run

```bash
# Check AI insights in database
psql -c "SELECT COUNT(*) FROM ai_insights WHERE status='active' AND expires_at > NOW();"

# Check if market_ids in insights exist in markets table
psql -c "
SELECT COUNT(*) as total_insights,
       COUNT(m.id) as with_valid_market
FROM ai_insights ai
LEFT JOIN markets m ON ai.market_id = m.id
WHERE ai.status = 'active';
"

# If market_ids don't match, regenerate insights
python run_analysis.py
```

## Files to Edit

1. `app/api/routes/insights.py` - Fix the query filter (lines 45-55)
2. `frontend/src/app/(app)/analytics/page.tsx` - Fix language
3. `frontend/src/lib/types.ts` - Check PATTERN_LABELS for "Arb" text
