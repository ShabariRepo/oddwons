# OddWons - UI Fixes

---

## WHY IMAGES AREN'T SHOWING

The backend code fetches images, but **existing data doesn't have images yet**.

**Fix:** Re-run data collection:

```bash
railway run python -c "import asyncio; from app.services.data_collector import data_collector; asyncio.run(data_collector.run_collection())"
```

---

## TASK 1: Markets Page - Add Platform Color Gradient to Table Rows

**Keep the table layout**, but add a diagonal platform color indicator to each row.

**File:** `frontend/src/app/(app)/markets/page.tsx`

**Replace the `MarketRow` function with:**

```tsx
function MarketRow({ market }: { market: Market }) {
  const router = useRouter()
  const yesPrice = market.yes_price ? (market.yes_price * 100).toFixed(1) : '-'
  const noPrice = market.no_price ? (market.no_price * 100).toFixed(1) : '-'

  // Platform colors
  const platformColor = market.platform === 'kalshi' ? '#00D26A' : '#6366F1'
  const platformLogo = market.platform === 'kalshi' 
    ? '/logos/kalshi-logo.png' 
    : '/logos/polymarket-logo.png'

  const formatVolume = (vol?: number) => {
    if (!vol) return '-'
    if (vol >= 1000000) return `$${(vol / 1000000).toFixed(1)}M`
    if (vol >= 1000) return `$${(vol / 1000).toFixed(0)}K`
    return `$${vol.toFixed(0)}`
  }

  const handleRowClick = () => {
    router.push(`/markets/${market.id}`)
  }

  const handleExternalClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    const url = market.platform === 'kalshi'
      ? `https://kalshi.com/markets/${market.id}`
      : `https://polymarket.com/event/${market.id}`
    window.open(url, '_blank')
  }

  return (
    <tr 
      className="hover:bg-gray-50 cursor-pointer relative overflow-hidden" 
      onClick={handleRowClick}
    >
      <td className="px-4 py-4">
        <div className="flex items-start gap-3">
          {/* Platform logo + diagonal color bar */}
          <div className="relative flex items-center gap-2 shrink-0">
            <div 
              className="w-1 h-10 rounded-full"
              style={{ backgroundColor: platformColor }}
            />
            <Image
              src={platformLogo}
              alt={market.platform}
              width={20}
              height={20}
              className="rounded-sm"
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {market.title}
            </p>
            {market.category && (
              <p className="text-xs text-gray-500 mt-0.5">{market.category}</p>
            )}
          </div>
        </div>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-sm font-medium text-green-600">{yesPrice}¢</span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-sm font-medium text-red-600">{noPrice}¢</span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-sm text-gray-900">{formatVolume(market.volume)}</span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className={clsx(
          'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
          market.status === 'active'
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-800'
        )}>
          {market.status}
        </span>
      </td>
      {/* Diagonal gradient on the right side of row */}
      <td className="px-4 py-4 text-right relative">
        <div 
          className="absolute right-0 top-0 bottom-0 w-16 pointer-events-none"
          style={{
            background: `linear-gradient(115deg, transparent 0%, transparent 30%, ${platformColor}20 30%, ${platformColor}40 100%)`,
          }}
        />
        <button
          className="text-gray-400 hover:text-gray-600 relative z-10"
          onClick={handleExternalClick}
          title="Open on platform"
        >
          <ExternalLink className="w-4 h-4" />
        </button>
      </td>
    </tr>
  )
}
```

**Make sure Image is imported at the top:**
```tsx
import Image from 'next/image'
```

---

## TASK 2: Cross-Platform Page - Full Card Layout

**File:** `frontend/src/app/(app)/cross-platform/page.tsx`

**Replace `MatchCard` function with:**

```tsx
function MatchCard({ match }: { match: CrossPlatformMatch }) {
  const kalshiPercent = match.kalshi_yes_price ? Math.round(match.kalshi_yes_price) : 50
  const polyPercent = match.polymarket_yes_price ? Math.round(match.polymarket_yes_price) : 50
  const gapColor = Math.abs(match.price_gap_cents) >= 5 ? 'text-green-600' : 'text-yellow-600'

  return (
    <div className="relative pt-14 mt-12">
      {/* Floating Circle - Both logos for cross-platform */}
      <div className="absolute -top-10 left-1/2 -translate-x-1/2 z-20">
        <div className="w-20 h-20 rounded-full overflow-hidden border-4 border-white shadow-xl bg-gradient-to-br from-green-400 via-blue-500 to-purple-600">
          <div className="w-full h-full flex items-center justify-center">
            <div className="flex items-center -space-x-2">
              <Image src="/logos/kalshi-logo.png" alt="K" width={28} height={28} className="rounded-full border-2 border-white bg-white" />
              <Image src="/logos/polymarket-logo.png" alt="P" width={28} height={28} className="rounded-full border-2 border-white bg-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Card */}
      <div className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-shadow border border-gray-100 overflow-hidden">
        <div className="px-4 pt-10 pb-4">
          {/* Category + Gap */}
          <div className="flex items-center justify-between mb-2">
            {match.category && (
              <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                {match.category}
              </span>
            )}
            <span className={`text-sm font-bold ${gapColor}`}>
              {match.price_gap_cents.toFixed(1)}¢ gap
            </span>
          </div>

          {/* Topic */}
          <h3 className="font-semibold text-gray-900 text-center mb-3 line-clamp-2">
            {match.topic}
          </h3>

          {/* Platform price boxes */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-green-50 rounded-lg py-2 px-3 text-center border border-green-100">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Image src="/logos/kalshi-logo.png" alt="K" width={14} height={14} />
                <span className="text-xs text-green-700 font-medium">Kalshi</span>
              </div>
              <p className="text-2xl font-bold text-green-700">{kalshiPercent}%</p>
            </div>
            <div className="bg-indigo-50 rounded-lg py-2 px-3 text-center border border-indigo-100">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Image src="/logos/polymarket-logo.png" alt="P" width={14} height={14} />
                <span className="text-xs text-indigo-700 font-medium">Polymarket</span>
              </div>
              <p className="text-2xl font-bold text-indigo-700">{polyPercent}%</p>
            </div>
          </div>

          {/* Volume */}
          <p className="text-sm text-gray-500 text-center">
            ${(match.combined_volume / 1000).toFixed(0)}K combined
          </p>
        </div>

        {/* Diagonal Footer - Split colors */}
        <div className="relative h-10 overflow-hidden">
          <div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(115deg, #00D26A 0%, #00D26A 50%, #6366F1 50%, #6366F1 100%)',
            }}
          />
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <span className="text-white text-xs font-medium">Cross-Platform Match</span>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Replace `MatchCardSkeleton` with:**

```tsx
function MatchCardSkeleton() {
  return (
    <div className="relative pt-14 mt-12">
      <div className="absolute -top-10 left-1/2 -translate-x-1/2 z-20">
        <div className="w-20 h-20 rounded-full bg-gray-200 animate-pulse border-4 border-white shadow-xl" />
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 pt-10 pb-4 space-y-3">
          <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
          <div className="grid grid-cols-2 gap-3">
            <div className="h-16 bg-gray-200 rounded animate-pulse" />
            <div className="h-16 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <div className="h-10 bg-gray-100" />
      </div>
    </div>
  )
}
```

---

## TASK 3: Add image_url to Market Type

**File:** `frontend/src/lib/types.ts`

Add `image_url` to the Market interface:

```typescript
export interface Market {
  id: string
  title: string
  platform: string
  category?: string
  yes_price?: number
  no_price?: number
  volume?: number
  liquidity?: number
  status: string
  close_time?: string
  image_url?: string  // ADD THIS LINE
  created_at: string
  updated_at: string
}
```

---

## SUMMARY

| Task | File | Action |
|------|------|--------|
| Markets rows | `markets/page.tsx` | Add platform color bar + gradient to table rows (keep table layout) |
| Cross-platform cards | `cross-platform/page.tsx` | Replace with full card layout (floating circle + diagonal footer) |
| Market type | `lib/types.ts` | Add `image_url?: string` |
| **Get images** | Backend | Re-run data collection |

---

## PROMPT FOR CLAUDE CODE

```
Read chat.md and implement:

1. In markets/page.tsx - Keep the TABLE layout but update MarketRow to have a colored vertical bar on the left (Kalshi=#00D26A, Polymarket=#6366F1) and a subtle diagonal gradient on the right side of each row

2. In cross-platform/page.tsx - Replace MatchCard and MatchCardSkeleton with the full card layout (floating circle with both platform logos, diagonal split-color footer)

3. In lib/types.ts - Add image_url?: string to Market interface
```
