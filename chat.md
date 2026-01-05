# CRITICAL FRONTEND ISSUES - FIX IMMEDIATELY

## Overview

The frontend is connected but has major data and display issues that make the app look broken. These need to be fixed before any user sees this.

---

## Issue 1: Showing RESOLVED Markets (HIGHEST PRIORITY)

### What's Wrong
- Dashboard shows "Will Donald Trump be inaugurated?" at **100% YES**
- AI Highlights shows 3 markets all at 0% or 100%
- Markets list top results all show `100.0¢`

### Why This Matters
A "research companion" showing already-decided markets is **completely useless**. Users see resolved elections, finished games, expired predictions. This makes the app look broken and uninformed.

### How to Fix

**Backend - Add filter to all market queries:**
```sql
-- Add this WHERE clause to ALL market queries
WHERE yes_price BETWEEN 0.02 AND 0.98
  AND status = 'active'
  AND (close_time IS NULL OR close_time > NOW())
```

**Backend - Update resolved markets status:**
```sql
-- Run this to fix existing data
UPDATE markets 
SET status = 'resolved' 
WHERE yes_price < 0.02 OR yes_price > 0.98;

-- Also mark closed markets
UPDATE markets 
SET status = 'closed' WHERE close_time < NOW() AND status = 'active';
```

**API Endpoints to Fix:**
- `GET /api/v1/markets` - Filter out resolved
- `GET /api/v1/insights/ai` - Filter out resolved
- `GET /api/v1/dashboard/summary` - Filter out resolved
- `GET /api/v1/cross-platform/matches` - Filter out resolved

**Frontend - Add fallback filter:**
```typescript
// In case backend doesn't filter, add frontend safety
const activeMarkets = markets.filter(m => 
  m.yes_price > 0.02 && 
  m.yes_price < 0.98 &&
  m.status === 'active'
);
```

---

## Issue 2: Cross-Platform Data Not Loading

### What's Wrong
```
Header shows:     420 Total Matches
List shows:       "Showing 0 cross-platform matches"
Volume shows:     $0.0M (should be $42M+)
Avg Gap shows:    0¢
```

The stats in the header suggest data exists, but nothing renders in the list.

### ROOT CAUSE IDENTIFIED
The API returns a **flat array** but the frontend expects **`{ matches: [...], total: ..., total_volume: ... }`**.

**Backend returns:**
```json
[{match_id, topic, ...}, ...]
```

**Frontend expects:**
```json
{matches: [...], total: N, total_volume: N}
```

The frontend does `data?.matches?.filter()` → `undefined` because `data` is an array, not an object.

### How to Fix

**Fix `app/api/routes/cross_platform.py` - change `/matches` endpoint to return:**
```python
@router.get("/matches")
async def list_cross_platform_matches(...):
    service = CrossPlatformService(db)
    matches = await service.find_all_matches(min_volume=min_volume)
    
    match_list = [
        {
            "match_id": m.match_id,
            "topic": m.topic,
            "category": m.category,
            "kalshi_yes_price": (m.kalshi_price or 0) * 100,
            "polymarket_yes_price": (m.poly_price or 0) * 100,
            "kalshi_volume": m.kalshi_volume or 0,
            "polymarket_volume": m.poly_volume or 0,
            "price_gap_cents": abs((m.kalshi_price or 0) * 100 - (m.poly_price or 0) * 100),
            "gap_direction": "kalshi_higher" if (m.kalshi_price or 0) > (m.poly_price or 0) else "polymarket_higher",
            "combined_volume": (m.kalshi_volume or 0) + (m.poly_volume or 0),
            "similarity_score": m.similarity_score,
        }
        for m in matches
    ]
    
    total_volume = sum(m["combined_volume"] for m in match_list)
    
    return {
        "matches": match_list,
        "total": len(match_list),
        "total_volume": total_volume,
    }
```

---

## Issue 3: No Kalshi Markets Showing

### What's Wrong
- Analytics shows: Kalshi 71,989 markets, Polymarket 60,620
- But Markets list only shows "P" badges (Polymarket)
- AI Highlights only shows Polymarket markets

### How to Fix

**Check database:**
```sql
SELECT platform, COUNT(*), 
       COUNT(*) FILTER (WHERE yes_price BETWEEN 0.02 AND 0.98) as active_count
FROM markets 
GROUP BY platform;
```

**Check if Kalshi prices are valid (cents vs decimal issue):**
```sql
SELECT platform, 
       AVG(yes_price) as avg_price,
       MIN(yes_price) as min_price,
       MAX(yes_price) as max_price
FROM markets
WHERE status = 'active'
GROUP BY platform;
```

---

## Issue 4: Status Field Not Updated

### How to Fix

**Run migration:**
```sql
UPDATE markets SET status = 'resolved' WHERE (yes_price < 0.02 OR yes_price > 0.98) AND status = 'active';
UPDATE markets SET status = 'closed' WHERE close_time < NOW() AND status = 'active';
```

**Add to data_collector.py:**
```python
async def update_market_status(session):
    """Update status for resolved/closed markets."""
    await session.execute(text("""
        UPDATE markets 
        SET status = 'resolved' 
        WHERE (yes_price < 0.02 OR yes_price > 0.98)
          AND status = 'active'
    """))
    await session.execute(text("""
        UPDATE markets 
        SET status = 'closed' 
        WHERE close_time < NOW() 
          AND status = 'active'
    """))
    await session.commit()
```

---

## Issue 5: Wrong Language (Alpha Hunter → Companion)

### Language to Replace

| Don't Say | Say Instead |
|-----------|-------------|
| opportunity | highlight, insight |
| opportunities | highlights, insights |
| arbitrage | price comparison, price gap |
| arb | comparison |
| alpha | insight |
| bet, betting | position, trading |
| STRONG_BET | (remove entirely) |
| edge | context |

**Search command:**
```bash
grep -rn 'opportunit\|arbitrage\|STRONG_BET' frontend/src/
```

---

## Priority Order

| Priority | Issue | Fix |
|----------|-------|-----|
| 🔴 P0 | Cross-platform response shape | Change API to return `{matches: [...], total, total_volume}` |
| 🔴 P0 | Filter resolved markets | Add WHERE clause to all market queries |
| 🟠 P1 | Show Kalshi markets | Check platform filter and price conversion |
| 🟠 P1 | Update status field | Run SQL migration |
| 🟡 P2 | Fix language | Search and replace |

---

## Commands for Claude Code

```bash
# Start here - read this file
cat chat.md

# Then fix the cross-platform API response shape in:
# app/api/routes/cross_platform.py

# Then run SQL to fix market status:
# UPDATE markets SET status = 'resolved' WHERE yes_price < 0.02 OR yes_price > 0.98;

# Then search for wrong language:
grep -rn 'opportunit\|arbitrage' frontend/src/
```
