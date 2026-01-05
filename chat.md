# FIX: AI Analysis Generating Insights for Resolved Markets

## Root Cause Found

The issue is **upstream** - `run_analysis.py` is generating insights for already-resolved markets.

In `app/services/patterns/engine.py`, the `load_market_data()` function doesn't filter by price:

```python
# Current code (BROKEN)
result = await session.execute(
    select(Market)
    .where(Market.status == "active")
    .where(Market.volume >= min_volume)  # No price filter!
    ...
)
```

So markets at 100% or 0% (like "Trump inauguration") are being analyzed and getting insights generated.

## The Fix

### Step 1: Add price filter to `load_market_data()`

In `app/services/patterns/engine.py`, update the `load_market_data` method (~line 45):

```python
async def load_market_data(
    self,
    session: AsyncSession,
    limit: int = 10000,
    history_points: int = 20,
    min_volume: float = 1000
) -> List[MarketData]:
    """Load market data with history from database."""
    
    # Get active markets with minimum volume AND valid prices
    result = await session.execute(
        select(Market)
        .where(Market.status == "active")
        .where(Market.volume >= min_volume)
        .where(Market.yes_price > 0.02)   # ADD: Filter out resolved (0%)
        .where(Market.yes_price < 0.98)   # ADD: Filter out resolved (100%)
        .order_by(Market.volume.desc().nullslast())
        .limit(limit)
    )
    markets = result.scalars().all()
    # ... rest of method
```

### Step 2: Clear stale insights from database

```sql
-- Delete insights for resolved markets
DELETE FROM ai_insights 
WHERE (current_odds->>'yes')::float < 0.02 
   OR (current_odds->>'yes')::float > 0.98
   OR (current_odds->>'yes')::float IS NULL;

-- Or just delete all and regenerate
DELETE FROM ai_insights;
```

### Step 3: Re-run analysis to generate fresh insights

```bash
cd ~/Desktop/code/oddwons
source venv/bin/activate
set -a && source .env && set +a
python run_analysis.py
```

## Why This Is Better Than Filtering at Display Time

| Approach | Pros | Cons |
|----------|------|------|
| Filter in `load_market_data()` | Prevents bad data at source | Need to re-run analysis |
| Filter in API endpoint | Quick fix | Still storing useless data |
| Shorter expiry time | Helps freshness | Doesn't prevent resolved markets |

**Fixing at the source is the right approach** - don't generate insights for resolved markets in the first place.

## Optional: Also Shorten Expiry Time

In `save_market_highlight()` (~line 280), consider reducing expiry from 24h to 8h:

```python
expires_at=datetime.utcnow() + timedelta(hours=8),  # Was 24
```

This ensures insights refresh more frequently, but the real fix is the price filter above.

---

## Commands to Run

```bash
# 1. Edit app/services/patterns/engine.py
# Add .where(Market.yes_price > 0.02).where(Market.yes_price < 0.98)
# to the load_market_data query

# 2. Clear old insights
psql -c "DELETE FROM ai_insights;"

# 3. Regenerate with fix in place
cd ~/Desktop/code/oddwons
source venv/bin/activate
set -a && source .env && set +a
python run_analysis.py

# 4. Verify new insights have valid prices
psql -c "
SELECT market_title, current_odds->>'yes' as yes_price 
FROM ai_insights 
WHERE status = 'active' 
ORDER BY created_at DESC 
LIMIT 10;
"
```

## Files to Edit

1. **`app/services/patterns/engine.py`** - Add price filter to `load_market_data()` (~line 45)
2. Optionally: Reduce `expires_at` from 24h to 8h (~line 280)
