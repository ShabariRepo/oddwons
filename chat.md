# OddWons - Critical Fixes

---

## ISSUE 1: Trial Users Should Get FULL Access (PRO-level)

**Problem:** The welcome email says "Full access to all features" but trial users are being tier-gated based on their selected plan tier. A user trialing BASIC only sees BASIC features, which contradicts the promise.

**Fix:** When `subscription_status == 'trialing'`, treat user as PRO tier for feature access.

### Backend Logic Change

**In every place that checks tier for gating, add trial check:**

```python
def get_effective_tier(user) -> SubscriptionTier:
    """Get the effective tier for feature access.
    
    Trial users get FULL (PRO) access.
    Active subscribers get their paid tier.
    Everyone else gets FREE.
    """
    from app.models.user import SubscriptionStatus, SubscriptionTier
    
    # Trial = full access (PRO)
    if user.subscription_status == SubscriptionStatus.TRIALING:
        return SubscriptionTier.PRO
    
    # Active subscription = their tier
    if user.subscription_status == SubscriptionStatus.ACTIVE:
        return user.subscription_tier or SubscriptionTier.FREE
    
    # Everything else (cancelled, expired, null) = FREE
    return SubscriptionTier.FREE
```

### Files to Update

**1. `app/api/routes/insights.py`**

Replace all `tier = user.subscription_tier` with:

```python
from app.services.auth import get_effective_tier

# In get_ai_insights()
tier = get_effective_tier(user)

# In get_insight_detail()
tier = get_effective_tier(user)

# In get_daily_digest()
tier = get_effective_tier(user)
```

**2. `app/api/routes/markets.py`**

In the `get_market` endpoint, use effective tier:

```python
from app.services.auth import get_effective_tier

# In get_market()
tier = get_effective_tier(current_user) if current_user else SubscriptionTier.FREE
```

**3. `app/services/auth.py`**

Add the helper function:

```python
from app.models.user import User, SubscriptionStatus, SubscriptionTier

def get_effective_tier(user: User) -> SubscriptionTier:
    """Get the effective tier for feature access.
    
    Trial users get FULL (PRO) access - as promised in welcome email.
    Active subscribers get their paid tier.
    Everyone else gets FREE.
    """
    if not user:
        return SubscriptionTier.FREE
    
    # Trial = full access (PRO level)
    if user.subscription_status == SubscriptionStatus.TRIALING:
        return SubscriptionTier.PRO
    
    # Active subscription = their paid tier
    if user.subscription_status == SubscriptionStatus.ACTIVE:
        return user.subscription_tier or SubscriptionTier.FREE
    
    # Cancelled, expired, past_due, null = FREE
    return SubscriptionTier.FREE
```

**4. Also add `get_current_user_optional` to `app/services/auth.py`:**

```python
from fastapi.security import OAuth2PasswordBearer

# Add this scheme that doesn't require auth
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

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
```

---

## ISSUE 2: Market Detail Page Not Tier-Gated

**Problem:** `/markets/{id}` returns ALL AI insight fields without checking user tier.

**File:** `app/api/routes/markets.py`

**Fix:** Update `get_market` to use authentication and tier-gate AI insight fields.

Add imports at top:
```python
from typing import Optional
from app.models.user import User, SubscriptionTier
from app.services.auth import get_current_user_optional, get_effective_tier
```

Update the function signature and add tier-gating:

```python
@router.get("/{market_id}")
async def get_market(
    market_id: str,
    history_limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # ... existing market fetch code ...

    # Get effective tier (trial = PRO)
    tier = get_effective_tier(current_user) if current_user else SubscriptionTier.FREE

    # Build tier-gated AI insight data
    ai_insight_data = None
    if ai_insight:
        # Base data - ALL TIERS
        ai_insight_data = {
            "id": ai_insight.id,
            "summary": ai_insight.summary,
            "current_odds": ai_insight.current_odds,
            "implied_probability": ai_insight.implied_probability,
            "created_at": ai_insight.created_at.isoformat() if ai_insight.created_at else None,
        }

        # BASIC+ get volume and movement
        if tier != SubscriptionTier.FREE:
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

    # ... rest of response building ...
    
    return {
        # ... existing fields ...
        "ai_insight": ai_insight_data,
        "tier": tier.value if tier else "free",
    }
```

---

## ISSUE 3: External Links to Kalshi/Polymarket Don't Work

**Problem:** 
- Polymarket URLs use condition_id but need SLUG
- Kalshi URLs use market ticker but need EVENT ticker

**Fix in `app/services/data_collector.py`:**

Add URL helper functions:

```python
import re

def get_kalshi_url(ticker: str, event_ticker: str = None) -> str:
    """Get Kalshi URL. Uses event ticker for /events/ URL."""
    if event_ticker:
        return f"https://kalshi.com/events/{event_ticker}"
    # Fallback: extract event ticker from market ticker
    # KXOSCARNOMPIC-26-WIC -> KXOSCARNOMPIC
    if ticker:
        match = re.match(r'^([A-Z]+(?:-[A-Z]+)*)', ticker)
        if match:
            return f"https://kalshi.com/events/{match.group(1)}"
    return f"https://kalshi.com/markets/{ticker}"

def get_polymarket_url(slug: str = None, condition_id: str = None) -> str:
    """Get Polymarket URL. Uses slug if available."""
    if slug:
        return f"https://polymarket.com/event/{slug}"
    # condition_id doesn't work for URLs
    return None
```

**When saving markets, populate the `url` field:**

```python
# For Kalshi
market_url = get_kalshi_url(market_data.ticker, event_ticker)

# For Polymarket  
market_url = get_polymarket_url(
    slug=event_data.get('slug'),
    condition_id=market_data.condition_id
)
```

**Also update `app/services/polymarket_client.py`** to capture the slug:

```python
# In PolymarketMarketData dataclass, add:
slug: Optional[str] = None

# When parsing, extract slug:
slug=market.get("slug") or event.get("slug"),
```

---

## ISSUE 4: Search Bar Doesn't Work

**Problem:** The search bar in the header is a placeholder.

**Fix:** Either make it functional or remove it.

**Option A - Make functional:**

```tsx
// In the header component
const handleSearch = (e: React.FormEvent) => {
  e.preventDefault()
  if (query.trim()) {
    router.push(`/markets?search=${encodeURIComponent(query.trim())}`)
  }
}
```

**Option B - Remove it** if search isn't a priority feature right now.

---

## ISSUE 5: Cross-Platform Cards Not Clickable

**Problem:** Cards have `cursor-pointer` but no click action.

**Fix:** Add external link buttons to the footer.

**File:** `frontend/src/app/(app)/cross-platform/page.tsx`

Update the `MatchCard` footer to include clickable links:

```tsx
{/* Diagonal Footer with links */}
<div className="relative h-12 overflow-hidden">
  <div
    className="absolute inset-0"
    style={{
      background: 'linear-gradient(115deg, #00D26A 0%, #00D26A 50%, #6366F1 50%, #6366F1 100%)',
    }}
  />
  <div className="absolute inset-0 flex items-center justify-between px-4 z-10">
    {match.kalshi_market_id && (
      <a
        href={`https://kalshi.com/events/${match.kalshi_market_id.replace('kalshi_', '').split('-')[0]}`}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="text-white text-xs font-medium hover:underline flex items-center gap-1"
      >
        Kalshi <ExternalLink className="w-3 h-3" />
      </a>
    )}
    {match.polymarket_market_id && (
      <a
        href={`https://polymarket.com/event/${match.polymarket_slug || ''}`}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="text-white text-xs font-medium hover:underline flex items-center gap-1"
      >
        Polymarket <ExternalLink className="w-3 h-3" />
      </a>
    )}
  </div>
</div>
```

Note: We need to store `polymarket_slug` in the CrossPlatformMatch model/response for the URL to work.

---

## ISSUE 6: Frontend Upgrade Prompts on Market Detail

**File:** `frontend/src/app/(app)/markets/[id]/page.tsx`

Show upgrade prompts when content is gated:

```tsx
{/* Show upgrade prompt if content is gated */}
{!ai_insight.analyst_note && data.tier !== 'pro' && (
  <div className="p-3 bg-gray-50 rounded-lg mb-4 text-sm text-gray-500">
    <span className="font-medium">Full AI analysis</span> - <Link href="/settings" className="text-primary-600 hover:underline">Upgrade to Pro</Link>
  </div>
)}
```

---

## SUMMARY

| Issue | Priority | Fix |
|-------|----------|-----|
| 1. Trial = Full Access | **CRITICAL** | Add `get_effective_tier()` - trial users get PRO |
| 2. Market detail tier-gating | **HIGH** | Add auth + tier-gate AI insight in markets.py |
| 3. Broken external URLs | **HIGH** | Use event ticker (Kalshi) and slug (Polymarket) |
| 4. Search bar | LOW | Make functional or remove |
| 5. Cross-platform cards | MEDIUM | Add external links to footer |
| 6. Frontend upgrade prompts | LOW | Show gated content hints |

---

## HOW STRIPE WEBHOOKS WORK (Already Implemented ✅)

Your webhook handler in `app/api/routes/billing.py` already handles these events:

| Stripe Event | Your Handler | Updates |
|--------------|--------------|---------|
| `customer.subscription.created` | `handle_subscription_created()` | Sets `subscription_status` to ACTIVE or TRIALING |
| `customer.subscription.updated` | `handle_subscription_updated()` | Updates status (active, past_due, canceled, trialing) |
| `customer.subscription.deleted` | `handle_subscription_deleted()` | Sets status to INACTIVE, tier to FREE |
| `invoice.payment_failed` | Sends email | No status change |
| `invoice.paid` | Logs | No status change |

**Status mapping in your code:**
```python
status_map = {
    "active": SubscriptionStatus.ACTIVE,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "trialing": SubscriptionStatus.TRIALING,
    "unpaid": SubscriptionStatus.INACTIVE,
}
```

**Production is working** - webhooks hit `https://oddwons.ai/api/v1/billing/webhook`

---

## LOCAL DEVELOPMENT: Stripe CLI Setup

**Problem:** No webhook in Stripe sandbox means local dev doesn't receive subscription updates.

### Setup Stripe CLI

```bash
# 1. Install Stripe CLI
brew install stripe/stripe-cli/stripe

# 2. Login to your Stripe account
stripe login

# 3. Forward webhooks to your local server
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

This outputs a webhook signing secret like:
```
Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
```

### Add to local `.env`

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### Test it works

```bash
# In another terminal, trigger a test event
stripe trigger customer.subscription.created
```

You should see:
- Stripe CLI shows the event was forwarded
- Your FastAPI logs show "Received Stripe webhook: customer.subscription.created"

### Alternative: Manual Sync

If you don't want to set up Stripe CLI, call the sync endpoint after checkout:

```bash
# After completing checkout, sync from Stripe
curl -X POST http://localhost:8000/api/v1/billing/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

This pulls the current subscription status directly from Stripe API.

### Quick Testing: Direct DB Update

For fast local testing without Stripe:

```sql
-- Set user to trialing (full access)
UPDATE users SET subscription_status = 'trialing', subscription_tier = 'BASIC' WHERE email = 'test@example.com';

-- Set user to active paid tier
UPDATE users SET subscription_status = 'active', subscription_tier = 'PREMIUM' WHERE email = 'test@example.com';

-- Set user to free (trial/subscription ended)
UPDATE users SET subscription_status = 'inactive', subscription_tier = 'FREE' WHERE email = 'test@example.com';
```

---

## PROMPT FOR CLAUDE CODE

```
Read chat.md and implement these fixes in order of priority:

1. TRIAL = FULL ACCESS (CRITICAL):
   - Add get_effective_tier() function to app/services/auth.py
   - If subscription_status == 'trialing', return PRO tier (full access)
   - If subscription_status == 'active', return their paid tier
   - Otherwise return FREE
   - Update app/api/routes/insights.py to use get_effective_tier(user) instead of user.subscription_tier
   - Update app/api/routes/markets.py get_market endpoint to use get_effective_tier()

2. MARKET DETAIL TIER-GATING:
   - Add get_current_user_optional to app/services/auth.py
   - Update get_market in markets.py to accept optional auth and tier-gate AI insight fields

3. FIX EXTERNAL URLS:
   - In data_collector.py, store correct URLs during collection
   - Kalshi: https://kalshi.com/events/{EVENT_TICKER}
   - Polymarket: https://polymarket.com/event/{SLUG}

4. CROSS-PLATFORM CARDS:
   - Add external link buttons to the card footer in cross-platform/page.tsx

5. SEARCH BAR:
   - Either connect to /markets?search= or remove the non-functional element
```
