# OddWons - Critical Fixes

---

## ISSUE 1: Market Detail Page Shows Premium Content to Basic Users (BUG!)

**Problem:** The `/markets/{id}` endpoint returns ALL AI insight fields without checking user tier. A BASIC user can see analyst_note, movement_context, upcoming_catalyst, and source_articles.

**File:** `app/api/routes/markets.py`

**Fix:** Add authentication and tier-gating to the market detail endpoint.

**Replace the `get_market` function (around line 150) with:**

```python
@router.get("/{market_id}")
async def get_market(
    market_id: str,
    history_limit: int = Query(100, ge=1, le=1000, description="Number of historical snapshots"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get full market details with price history, AI insight (if exists), and cross-platform match.
    AI insight fields are tier-gated.
    """
    from app.models.cross_platform_match import CrossPlatformMatch
    from app.models.user import SubscriptionTier

    result = await db.execute(
        select(Market).where(Market.id == market_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Fetch snapshots
    snapshot_result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .limit(history_limit)
    )
    snapshots = snapshot_result.scalars().all()

    # Compute enriched fields for this single market
    enriched = await compute_enriched_fields([market], db)

    # Build price history
    price_history = [
        {
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "yes_price": s.yes_price,
            "no_price": s.no_price,
            "volume": s.volume,
            "volume_24h": s.volume_24h,
        }
        for s in reversed(snapshots)
    ]

    # Check for AI insight
    ai_insight_result = await db.execute(
        select(AIInsight)
        .where(AIInsight.market_id == market_id)
        .where(AIInsight.status == "active")
        .order_by(AIInsight.created_at.desc())
        .limit(1)
    )
    ai_insight = ai_insight_result.scalar_one_or_none()

    # Get user tier for gating
    tier = current_user.subscription_tier if current_user else None

    # Build tier-gated AI insight data
    ai_insight_data = None
    if ai_insight:
        # Base data - ALL TIERS see summary
        ai_insight_data = {
            "id": ai_insight.id,
            "summary": ai_insight.summary,
            "current_odds": ai_insight.current_odds,
            "implied_probability": ai_insight.implied_probability,
            "created_at": ai_insight.created_at.isoformat() if ai_insight.created_at else None,
        }

        # BASIC+ get volume and movement
        if tier and tier != SubscriptionTier.FREE:
            ai_insight_data["volume_note"] = ai_insight.volume_note
            ai_insight_data["recent_movement"] = ai_insight.recent_movement

        # PREMIUM+ get full context
        if tier in [SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
            ai_insight_data["movement_context"] = ai_insight.movement_context
            ai_insight_data["upcoming_catalyst"] = ai_insight.upcoming_catalyst
            ai_insight_data["source_articles"] = ai_insight.source_articles

        # PRO only gets analyst notes
        if tier == SubscriptionTier.PRO:
            ai_insight_data["analyst_note"] = ai_insight.analyst_note

    # Check for cross-platform match
    cross_platform = None
    match_result = await db.execute(
        select(CrossPlatformMatch)
        .where(
            (CrossPlatformMatch.kalshi_market_id == market_id) |
            (CrossPlatformMatch.polymarket_market_id == market_id)
        )
        .limit(1)
    )
    cross_match = match_result.scalar_one_or_none()
    if cross_match:
        cross_platform = {
            "match_id": cross_match.match_id,
            "topic": cross_match.topic,
            "kalshi_market_id": cross_match.kalshi_market_id,
            "polymarket_market_id": cross_match.polymarket_market_id,
            "kalshi_price": cross_match.kalshi_yes_price,
            "polymarket_price": cross_match.polymarket_yes_price,
            "price_gap": abs(
                (cross_match.kalshi_yes_price or 0) - (cross_match.polymarket_yes_price or 0)
            ) if cross_match.kalshi_yes_price and cross_match.polymarket_yes_price else None,
        }

    # Use stored market URL (should be set during collection)
    market_url = market.url

    # Build response
    enriched_market = enriched[0]

    # Get volume_24h from latest snapshot
    volume_24h = None
    if snapshots:
        volume_24h = snapshots[0].volume_24h

    return {
        "market": {
            "id": enriched_market.id,
            "title": enriched_market.title,
            "platform": enriched_market.platform.value if hasattr(enriched_market.platform, 'value') else enriched_market.platform,
            "yes_price": enriched_market.yes_price,
            "no_price": enriched_market.no_price,
            "volume": enriched_market.volume,
            "volume_24h": volume_24h,
            "status": enriched_market.status,
            "category": enriched_market.category,
            "close_time": enriched_market.close_time.isoformat() if enriched_market.close_time else None,
            "url": market_url,
            "implied_probability": enriched_market.implied_probability,
            "price_change_24h": enriched_market.price_change_24h,
            "price_change_7d": enriched_market.price_change_7d,
            "volume_rank": enriched_market.volume_rank,
            "has_ai_highlight": enriched_market.has_ai_highlight,
            "created_at": enriched_market.created_at.isoformat() if enriched_market.created_at else None,
            "updated_at": enriched_market.updated_at.isoformat() if enriched_market.updated_at else None,
        },
        "price_history": price_history,
        "ai_insight": ai_insight_data,
        "cross_platform": cross_platform,
        "tier": tier.value if tier else "free",
    }
```

**Also add these imports at the top of markets.py:**

```python
from typing import Optional
from app.models.user import User, SubscriptionTier
from app.services.auth import get_current_user_optional
```

**Create the `get_current_user_optional` function in `app/services/auth.py`:**

```python
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

# Also add this OAuth scheme that doesn't require auth:
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
```

---

## ISSUE 2: External Links to Kalshi/Polymarket Don't Work

**Problem:** 
- Polymarket URLs need the market SLUG, not the condition_id
- Kalshi URLs need the EVENT ticker, not the market ticker

**Current broken examples:**
- Kalshi: `https://kalshi.com/markets/KXOSCARNOMPIC-26-WIC` → 404
- Polymarket: `https://polymarket.com/event/0xe93c89c41d...` → 404

**Correct formats:**
- Kalshi: `https://kalshi.com/events/KXOSCARNOMPIC` (event ticker, not market ticker)
- Polymarket: `https://polymarket.com/event/slug-name-here` (slug, not condition_id)

### Fix Part A: Store correct URLs during data collection

**File:** `app/services/data_collector.py`

Find where markets are saved and ensure the `url` field is populated correctly from the API response.

**For Polymarket** - the API returns a `slug` field. Use it:
```python
# In polymarket collection
market_url = f"https://polymarket.com/event/{event_data.get('slug', '')}"
```

**For Kalshi** - extract event ticker from market ticker:
```python
# In kalshi collection  
# Market ticker: KXOSCARNOMPIC-26-WIC
# Event ticker: KXOSCARNOMPIC (everything before first hyphen followed by numbers)
import re
event_ticker = re.match(r'^([A-Z]+)', market_data.ticker).group(1) if market_data.ticker else ''
market_url = f"https://kalshi.com/events/{event_ticker}"
```

### Fix Part B: Update data_collector.py

**File:** `app/services/data_collector.py`

Find the section where markets are saved to the database and add URL construction:

```python
# For Kalshi markets - extract event ticker
def get_kalshi_url(ticker: str) -> str:
    """Get Kalshi event URL from market ticker."""
    # Market ticker format: KXOSCARNOMPIC-26-WIC or FED-26JAN29
    # We need just the event part
    if not ticker:
        return None
    # Try to find event ticker (letters before first number or hyphen)
    import re
    match = re.match(r'^([A-Z]+(?:-[A-Z]+)?)', ticker)
    if match:
        event_ticker = match.group(1)
        return f"https://kalshi.com/events/{event_ticker}"
    return f"https://kalshi.com/markets/{ticker}"

# For Polymarket markets - use slug from API
def get_polymarket_url(slug: str, condition_id: str) -> str:
    """Get Polymarket URL from slug or condition_id."""
    if slug:
        return f"https://polymarket.com/event/{slug}"
    return f"https://polymarket.com/markets/{condition_id}"
```

### Fix Part C: Update Polymarket client to return slug

**File:** `app/services/polymarket_client.py`

Ensure the `PolymarketMarketData` schema includes `slug`:

```python
@dataclass
class PolymarketMarketData:
    # ... existing fields ...
    slug: Optional[str] = None  # ADD THIS
```

And populate it during parsing:
```python
slug=market.get("slug") or event.get("slug"),
```

---

## ISSUE 3: Search Bar Doesn't Work

**Problem:** The search bar in the header is just a placeholder and doesn't actually search anything.

**File:** `frontend/src/components/Header.tsx` or wherever the search bar is

**Option A: Make it functional** - Connect to markets search API:

```tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'

function SearchBar() {
  const [query, setQuery] = useState('')
  const router = useRouter()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/markets?search=${encodeURIComponent(query.trim())}`)
    }
  }

  return (
    <form onSubmit={handleSearch} className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
      <input
        type="text"
        placeholder="Search markets..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      />
    </form>
  )
}
```

**Option B: Remove it** - If search isn't needed, remove the non-functional element to avoid confusing users.

---

## ISSUE 4: Frontend Market Detail - Show Upgrade Prompts

**File:** `frontend/src/app/(app)/markets/[id]/page.tsx`

Update the AI insight section to show upgrade prompts for gated content:

```tsx
{/* AI Insight - if exists */}
{ai_insight && (
  <div className="card border-l-4 border-purple-500">
    <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
      <Brain className="w-5 h-5 text-purple-500" />
      AI Analysis
    </h2>
    
    {/* Summary - all tiers */}
    {ai_insight.summary && (
      <p className="text-gray-600 mb-3">{ai_insight.summary}</p>
    )}
    
    {/* Analyst note - PRO only */}
    {ai_insight.analyst_note ? (
      <p className="text-gray-700 whitespace-pre-wrap mb-4">{ai_insight.analyst_note}</p>
    ) : data.tier !== 'pro' && (
      <div className="p-3 bg-gray-50 rounded-lg mb-4 text-sm text-gray-500">
        <span className="font-medium">Full AI analysis</span> available on Pro tier
      </div>
    )}

    {/* Upcoming Catalyst - PREMIUM+ */}
    {ai_insight.upcoming_catalyst ? (
      <div className="p-3 bg-yellow-50 rounded-lg mb-4">
        <p className="text-sm font-medium text-yellow-800">Upcoming Catalyst</p>
        <p className="text-yellow-700 mt-1">{ai_insight.upcoming_catalyst}</p>
      </div>
    ) : data.tier === 'basic' && (
      <div className="p-3 bg-gray-50 rounded-lg mb-4 text-sm text-gray-500">
        <span className="font-medium">Upcoming catalysts</span> available on Premium+
      </div>
    )}

    {/* Movement Context - PREMIUM+ */}
    {ai_insight.movement_context ? (
      <div className="p-3 bg-blue-50 rounded-lg mb-4">
        <p className="text-sm font-medium text-blue-800">Why It Moved</p>
        <p className="text-blue-700 mt-1">{ai_insight.movement_context}</p>
      </div>
    ) : data.tier === 'basic' && (
      <div className="p-3 bg-gray-50 rounded-lg mb-4 text-sm text-gray-500">
        <span className="font-medium">Movement context</span> available on Premium+
      </div>
    )}

    {/* Source Articles - PREMIUM+ */}
    {ai_insight.source_articles && ai_insight.source_articles.length > 0 ? (
      <div className="border-t pt-4">
        <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
          <Newspaper className="w-4 h-4" />
          Sources (our homework)
        </p>
        <div className="space-y-2">
          {ai_insight.source_articles.map((article: any, i: number) => (
            <div key={i} className="text-sm text-gray-600">
              {article.title} <span className="text-gray-400">({article.source})</span>
            </div>
          ))}
        </div>
      </div>
    ) : data.tier === 'basic' && (
      <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-500">
        <span className="font-medium">Source articles</span> available on Premium+
      </div>
    )}

    <Link
      href={`/insights/${ai_insight.id}`}
      className="text-sm text-purple-600 hover:underline mt-3 inline-block"
    >
      View full insight
    </Link>
  </div>
)}
```

---

## SUMMARY

| Issue | File | Fix |
|-------|------|-----|
| 1. Tier gating on market detail | `app/api/routes/markets.py` | Add user auth + tier-gate ai_insight fields |
| 1b. Optional auth helper | `app/services/auth.py` | Add `get_current_user_optional` |
| 2. Broken Kalshi URLs | `app/services/data_collector.py` | Extract event ticker, use `/events/` URL |
| 2. Broken Polymarket URLs | `app/services/data_collector.py` | Use slug field from API |
| 3. Search bar | `frontend/src/components/Header.tsx` | Either make functional or remove |
| 4. Frontend upgrade prompts | `frontend/src/app/(app)/markets/[id]/page.tsx` | Show upgrade prompts for gated content |

---

## PROMPT FOR CLAUDE CODE

```
Read chat.md and implement all 4 fixes:

1. BACKEND TIER GATING (CRITICAL):
   - In app/api/routes/markets.py, update get_market endpoint to tier-gate AI insight fields
   - Add get_current_user_optional to app/services/auth.py
   - FREE: only summary, current_odds, implied_probability
   - BASIC: add volume_note, recent_movement  
   - PREMIUM: add movement_context, upcoming_catalyst, source_articles
   - PRO: add analyst_note

2. FIX EXTERNAL URLS:
   - In data_collector.py, construct correct URLs:
     - Kalshi: https://kalshi.com/events/{EVENT_TICKER} (not market ticker)
     - Polymarket: https://polymarket.com/event/{SLUG} (not condition_id)
   - Store the URL in the market.url field during collection

3. SEARCH BAR:
   - Either connect it to /markets?search= or remove it if not needed

4. FRONTEND UPGRADE PROMPTS:
   - In markets/[id]/page.tsx, show "available on Premium+" messages for gated content
```
