# OddWons - COMPLETE FIX INSTRUCTIONS

## ✅ ALL ISSUES COMPLETED (Jan 9, 2026)

All 6 issues have been implemented and committed:
- [x] Issue 1: Kalshi images - Added `get_event_metadata()` method
- [x] Issue 2: Circle image bigger - Changed to `w-20 h-20`, `-top-10`, `pt-14 mt-12`
- [x] Issue 3: Dashboard cards - Replaced InsightCard with floating circle + diagonal footer
- [x] Issue 4: Sidebar trial badge - Removed `daysLeft > 0` check, defaults to 7
- [x] Issue 5: Settings NaN fix - Handles null `trial_end_date` gracefully
- [x] Issue 6: Backend /me endpoint - Now returns `trial_end_date` field

---

## ISSUE 1: Fetch Market Images from APIs

### Problem
Cards show letter fallback (S, K, R, F, W) instead of actual market images because:
- **Kalshi:** Images are in a **separate metadata endpoint**, not in the events/markets response
- **Polymarket:** Images should be in event response but may not be extracted correctly

### Fix 1A: Update Kalshi Client

**File:** `app/services/kalshi_client.py`

**Add this new method after `get_event_markets`:**

```python
async def get_event_metadata(self, event_ticker: str) -> Dict[str, Any]:
    """Fetch event metadata including image_url."""
    client = await self._get_client()
    try:
        response = await client.get(f"/events/{event_ticker}/metadata")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Kalshi event metadata error for {event_ticker}: {e}")
        return {}
```

**Update `fetch_all_markets` method - find the events loop (around line 95) and replace:**

```python
for event in events:
    event_ticker = event.get("event_ticker") or event.get("ticker")
    if not event_ticker:
        continue

    # Extract event image URL
    event_image_url = event.get("image_url") or event.get("image")
```

**With:**

```python
for event in events:
    event_ticker = event.get("event_ticker") or event.get("ticker")
    if not event_ticker:
        continue

    # Fetch event metadata to get image_url (Kalshi stores images in separate endpoint)
    event_image_url = None
    try:
        metadata = await self.get_event_metadata(event_ticker)
        event_image_url = metadata.get("image_url")
    except Exception as e:
        logger.debug(f"Could not fetch metadata for {event_ticker}: {e}")
    
    # Fallback to event fields if metadata failed
    if not event_image_url:
        event_image_url = event.get("image_url") or event.get("image")
```

### Fix 1B: Verify Polymarket Client

**File:** `app/services/polymarket_client.py`

In `parse_market` method, try multiple field names for image:

```python
event_image_url = (
    event.get("image") or 
    event.get("icon") or 
    event.get("image_url") or
    event.get("imageUrl") or
    event.get("banner") or
    event.get("thumbnail")
)
```

### Fix 1C: Add image_url to AIInsight Schema

**File:** `app/schemas/insight.py` (or wherever AIInsight is defined)

```python
class AIInsight(BaseModel):
    # ... existing fields ...
    image_url: Optional[str] = None
```

**File:** `frontend/src/lib/types.ts`

```typescript
export interface AIInsight {
  // ... existing fields ...
  image_url?: string;
}
```

---

## ISSUE 2: Circle Image Too Small & Not Overlapping Enough

### Problem
Circle is small (w-16 h-16) and only slightly overlapping the card.

### Fix

**Files to update:**
- `frontend/src/app/(app)/opportunities/page.tsx`
- `frontend/src/app/(app)/dashboard/page.tsx`

**In InsightCard, change:**

```tsx
{/* Container - MORE padding and margin */}
<div className="relative pt-14 mt-12">

  {/* Circle - BIGGER and overlap more */}
  <div className="absolute -top-10 left-1/2 -translate-x-1/2 z-20">
    <div className={`w-20 h-20 rounded-full overflow-hidden border-4 border-white shadow-xl bg-gradient-to-br ${platform.gradient}`}>
      {insight.image_url ? (
        <Image
          src={insight.image_url}
          alt=""
          width={80}
          height={80}
          className="object-cover w-full h-full"
          unoptimized
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-white text-2xl font-bold">
          {insight.market_title?.charAt(0) || '?'}
        </div>
      )}
    </div>
  </div>
```

**Key changes:**
- `pt-14 mt-12` (was pt-10 mt-8)
- `w-20 h-20` (was w-16 h-16)  
- `-top-10` (was -top-6)
- `width={80} height={80}` (was 64)
- `text-2xl` (was text-xl)

---

## ISSUE 3: Dashboard Cards Need Same Layout

### Problem
Dashboard has its OWN `InsightCard` function that doesn't have the floating circle + diagonal footer design.

### Fix

**File:** `frontend/src/app/(app)/dashboard/page.tsx`

**Replace the entire `InsightCard` function with:**

```tsx
function InsightCard({ insight }: { insight: AIInsight }) {
  const platformConfig = {
    kalshi: {
      color: '#00D26A',
      logo: '/logos/kalshi-logo.png',
      gradient: 'from-green-400 to-emerald-600',
    },
    polymarket: {
      color: '#6366F1',
      logo: '/logos/polymarket-logo.png',
      gradient: 'from-indigo-400 to-purple-600',
    },
  }

  const platform = platformConfig[insight.platform as keyof typeof platformConfig] || platformConfig.polymarket

  return (
    <Link href={`/insights/${insight.id}`}>
      <div className="relative pt-14 mt-12">
        {/* Floating Circular Image */}
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 z-20">
          <div className={`w-20 h-20 rounded-full overflow-hidden border-4 border-white shadow-xl bg-gradient-to-br ${platform.gradient}`}>
            {insight.image_url ? (
              <Image
                src={insight.image_url}
                alt=""
                width={80}
                height={80}
                className="object-cover w-full h-full"
                unoptimized
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white text-2xl font-bold">
                {insight.market_title?.charAt(0) || '?'}
              </div>
            )}
          </div>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-shadow cursor-pointer border border-gray-100 overflow-hidden">
          <div className="px-4 pt-10 pb-4">
            {insight.category && (
              <div className="flex justify-center mb-2">
                <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                  {insight.category}
                </span>
              </div>
            )}

            <h3 className="font-semibold text-gray-900 text-center mb-2 line-clamp-2">
              {insight.market_title}
            </h3>

            <p className="text-sm text-gray-600 mb-3 line-clamp-3">
              {insight.summary}
            </p>

            {insight.implied_probability && (
              <p className="text-sm text-primary-600 font-medium mb-2">
                {insight.implied_probability}
              </p>
            )}

            {insight.recent_movement && (
              <span className={`text-sm font-medium ${
                insight.recent_movement.includes('+') ? 'text-green-600' :
                insight.recent_movement.includes('-') ? 'text-red-600' : 'text-gray-500'
              }`}>
                {insight.recent_movement}
              </span>
            )}

            {insight.volume_note && (
              <p className="text-xs text-gray-500 mt-2">{insight.volume_note}</p>
            )}
          </div>

          {/* Diagonal Footer */}
          <div className="relative h-10 overflow-hidden">
            <div
              className="absolute inset-0"
              style={{
                background: `linear-gradient(115deg, white 0%, white 40%, ${platform.color} 40%, ${platform.color} 100%)`,
              }}
            />
            <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2 z-10">
              <Image
                src={platform.logo}
                alt={insight.platform}
                width={18}
                height={18}
                className="object-contain"
              />
              <span className="text-sm font-medium text-gray-700 capitalize">
                {insight.platform}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}
```

---

## ISSUE 4: Sidebar Still Shows "NO ACTIVE PLAN"

### Problem
`trial_end_date` is null, so `daysLeft = 0`, which fails the `daysLeft > 0` check.

### Fix

**File:** `frontend/src/components/Sidebar.tsx`

**Replace the tier badge logic (the `{(() => {` block) with:**

```tsx
{(() => {
  const status = user?.subscription_status?.toLowerCase()
  const userTier = user?.subscription_tier?.toLowerCase()

  const isTrialing = status === 'trialing'
  const isActive = status === 'active'
  const hasTier = !!userTier && userTier !== 'free'

  // Calculate days left - try multiple field names, default to 7
  const trialEndRaw = user?.trial_end_date || user?.trial_end || user?.subscription_end
  let daysLeft = 7
  
  if (trialEndRaw) {
    const trialEndDate = new Date(trialEndRaw)
    if (!isNaN(trialEndDate.getTime())) {
      daysLeft = Math.max(1, Math.ceil((trialEndDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
    }
  }

  // If trialing AND has a tier, ALWAYS show trial badge (removed daysLeft > 0 check)
  if (isTrialing && hasTier) {
    return (
      <TierBadge
        tier={userTier.toUpperCase() as 'BASIC' | 'PREMIUM' | 'PRO'}
        daysLeft={daysLeft}
      />
    )
  } else if (isActive && hasTier) {
    return (
      <TierBadge tier={userTier.toUpperCase() as 'BASIC' | 'PREMIUM' | 'PRO'} />
    )
  } else {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide">No Active Plan</p>
        <p className="text-sm text-gray-300 mt-1">Start your 7-day free trial</p>
        <Link
          href="/settings"
          className="mt-3 block text-center text-sm text-white bg-primary-600 hover:bg-primary-700 rounded-lg py-2 transition-colors"
        >
          Choose a Plan
        </Link>
      </div>
    )
  }
})()}
```

---

## ISSUE 5: Settings Shows "NaN days left"

### Problem
`new Date(undefined)` creates Invalid Date, causing NaN.

### Fix

**File:** `frontend/src/app/(app)/settings/page.tsx`

**Find the Current Plan section and replace the status text with:**

```tsx
<p className="text-sm text-gray-500">
  {(() => {
    const status = user?.subscription_status?.toLowerCase()
    if (status === 'trialing') {
      const trialEnd = user?.trial_end_date || user?.trial_end || user?.subscription_end
      if (trialEnd) {
        const endDate = new Date(trialEnd)
        if (!isNaN(endDate.getTime())) {
          const days = Math.max(0, Math.ceil((endDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
          return `Free trial - ${days} days left`
        }
      }
      return 'Free trial active'
    }
    if (status === 'active') return 'Active subscription'
    return 'Start a 7-day free trial below'
  })()}
</p>
```

---

## ISSUE 6: Backend Not Returning trial_end_date

### Fix

**File:** `app/api/routes/auth.py`

**Ensure `/me` endpoint returns trial fields:**

```python
@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "is_admin": current_user.is_admin,
        "subscription_tier": current_user.subscription_tier.value if current_user.subscription_tier else None,
        "subscription_status": current_user.subscription_status.value if current_user.subscription_status else "inactive",
        "subscription_end": current_user.subscription_end.isoformat() if current_user.subscription_end else None,
        "trial_end_date": current_user.trial_end.isoformat() if hasattr(current_user, 'trial_end') and current_user.trial_end else None,
        "trial_start": current_user.trial_start.isoformat() if hasattr(current_user, 'trial_start') and current_user.trial_start else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
```

**Check User model has columns (if missing, add migration):**

```python
# app/models/user.py
trial_start = Column(DateTime, nullable=True)
trial_end = Column(DateTime, nullable=True)
```

---

## SUMMARY - FILES TO MODIFY

### Backend:
1. `app/services/kalshi_client.py` - Add `get_event_metadata()`, call it in fetch loop
2. `app/services/polymarket_client.py` - Try multiple image field names
3. `app/schemas/insight.py` - Add `image_url` to AIInsight
4. `app/api/routes/auth.py` - Return `trial_end_date` in `/me`
5. `app/models/user.py` - Ensure `trial_start`, `trial_end` columns exist

### Frontend:
1. `frontend/src/lib/types.ts` - Add `image_url` to AIInsight type
2. `frontend/src/app/(app)/opportunities/page.tsx` - Bigger circle: `w-20 h-20`, `-top-10`, `pt-14 mt-12`
3. `frontend/src/app/(app)/dashboard/page.tsx` - Replace InsightCard with new design
4. `frontend/src/components/Sidebar.tsx` - Remove `daysLeft > 0` check, default to 7
5. `frontend/src/app/(app)/settings/page.tsx` - Handle null trial_end_date

---

## API REFERENCE

| Platform | Image Location | Endpoint |
|----------|----------------|----------|
| Kalshi | Separate metadata endpoint | `GET /events/{ticker}/metadata` → `{"image_url": "..."}` |
| Polymarket | In event response | `event.image` or `event.icon` from `/events` |
