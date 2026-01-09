# OddWons - Claude Code Tasks

_Last updated: January 8, 2025_

---

## CRITICAL ISSUES TO FIX

### ISSUE 1: Market Card Layout - Image Overlapping Top

The market cards need a new design where the market image floats/overlaps the top of the card (like a profile picture that sits half above, half inside the card).

**Current:** No image, or image inside card
**Wanted:** Circular/rounded image centered at top, overlapping the card boundary by ~50%

```
         ┌─────────┐
         │  IMAGE  │  ← Image overlaps card top
         │ (circle)│
    ┌────┴─────────┴────┐
    │                   │
    │   Market Title    │
    │   Details...      │
    │                   │
    ├───────────────────┤
    │[LOGO]▓▓▓▓▓▓▓▓▓▓▓▓▓│  ← Diagonal footer
    └───────────────────┘
```

**Implementation:**

```tsx
// MarketCard.tsx

<div className="relative pt-12 mt-8"> {/* Extra padding for overlapping image */}
  {/* Overlapping Image */}
  <div className="absolute -top-10 left-1/2 -translate-x-1/2 z-10">
    <div className="w-20 h-20 rounded-full border-4 border-white shadow-lg overflow-hidden bg-gradient-to-br from-gray-200 to-gray-300">
      {market.image_url ? (
        <Image src={market.image_url} alt="" fill className="object-cover" />
      ) : (
        <div className={`w-full h-full ${fallbackGradient}`} />
      )}
    </div>
  </div>
  
  {/* Card Body */}
  <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
    {/* Content with top padding to account for image */}
    <div className="pt-12 px-4 pb-4">
      <h3 className="font-semibold text-center">{market.title}</h3>
      {/* ... rest of content */}
    </div>
    
    {/* Diagonal Footer - see Issue 2 */}
  </div>
</div>
```

**Get images from APIs:**
- Kalshi: Check `image_url` field in event/market response
- Polymarket: Check `image` or `icon` field in event response

---

### ISSUE 2: Card Footer - Diagonal Gradient with Platform Logo

The card footer should have a diagonal/angled design with the platform logo on the left and the platform brand color filling diagonally to the right.

**Platform Assets:**
- Kalshi logo: `/logos/kalshi-logo.png`
- Kalshi color: `#00D26A` (mint green)
- Polymarket logo: `/logos/polymarket-logo.png`  
- Polymarket color: `#6366F1` (deep blue/indigo)

**Implementation using clip-path:**

```tsx
// Card Footer
<div className="relative h-12 overflow-hidden">
  {/* Background color layer - diagonal */}
  <div 
    className="absolute inset-0"
    style={{ 
      backgroundColor: platform === 'kalshi' ? '#00D26A' : '#6366F1',
      clipPath: 'polygon(30% 0, 100% 0, 100% 100%, 0% 100%)'
    }}
  />
  
  {/* Logo on left side */}
  <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2 z-10">
    <Image 
      src={platform === 'kalshi' ? '/logos/kalshi-logo.png' : '/logos/polymarket-logo.png'}
      alt={platform}
      width={24}
      height={24}
      className="object-contain"
    />
    <span className="text-sm font-medium text-gray-700 capitalize">{platform}</span>
  </div>
</div>
```

**Alternative using linear-gradient:**

```tsx
<div 
  className="h-12 flex items-center px-3"
  style={{
    background: platform === 'kalshi' 
      ? 'linear-gradient(115deg, white 35%, #00D26A 35%)'
      : 'linear-gradient(115deg, white 35%, #6366F1 35%)'
  }}
>
  <Image src={`/logos/${platform}-logo.png`} ... />
  <span>{platform}</span>
</div>
```

---

### ISSUE 3: Sidebar - Trial Days / Tier Badge NOT Showing

**Current:** Shows "NO ACTIVE PLAN - Start your 7-day free trial" even for subscribed users
**Wanted:** Dynamic badge based on user state

**Logic:**

```tsx
// In Sidebar.tsx - bottom section

{user.subscription_status === 'TRIALING' && user.trial_end ? (
  // ON TRIAL - Show countdown
  <div className="mx-3 mb-4 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl">
    <div className="flex items-center gap-2">
      <span className="text-lg">⏳</span>
      <div>
        <p className="text-sm font-semibold text-amber-800">
          {daysLeft} day{daysLeft !== 1 ? 's' : ''} left on trial
        </p>
        <p className="text-xs text-amber-600">{user.subscription_tier} plan</p>
      </div>
    </div>
  </div>
) : user.subscription_tier && user.subscription_tier !== 'FREE' && user.subscription_status === 'ACTIVE' ? (
  // PAID USER - Show tier ribbon with bubbles for PREMIUM/PRO
  <TierBadge tier={user.subscription_tier} />
) : (
  // FREE/NO SUBSCRIPTION - Show upgrade prompt
  <Link href="/settings" className="mx-3 mb-4 block p-3 bg-primary-500 text-white rounded-xl text-center">
    🚀 Start your 7-day free trial
  </Link>
)}
```

**Calculate days left:**
```tsx
const daysLeft = user.trial_end 
  ? Math.max(0, Math.ceil((new Date(user.trial_end).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
  : 0
```

---

### ISSUE 4: Settings Page - Current Plan Gold Sparkles NOT Working

**Current:** All plan cards look the same, no indication of current plan
**Wanted:** Current plan highlighted with gold border, sparkle animation, and "YOU" badge

**Implementation:**

```tsx
// settings/page.tsx

{tiers.map((tier) => {
  const isCurrentPlan = user?.subscription_tier?.toUpperCase() === tier.id.toUpperCase()
  
  return (
    <div key={tier.id} className="relative">
      {/* Sparkle container for current plan */}
      {isCurrentPlan && <SparkleEffect />}
      
      <div className={`relative p-6 rounded-2xl border-2 transition-all ${
        isCurrentPlan 
          ? 'border-yellow-400 bg-gradient-to-b from-yellow-50 to-white shadow-[0_0_30px_rgba(255,215,0,0.3)]' 
          : 'border-gray-200 bg-white'
      }`}>
        
        {/* "YOU" Badge for current plan */}
        {isCurrentPlan && (
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-20">
            <span className="bg-gradient-to-r from-yellow-400 to-amber-500 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg">
              ✨ YOU
            </span>
          </div>
        )}
        
        {/* Plan content */}
        <h3>{tier.name}</h3>
        <p>${tier.price}/month</p>
        {/* features... */}
        
        {/* Button - CONDITIONAL */}
        {isCurrentPlan ? (
          <button disabled className="w-full py-3 bg-gray-100 text-gray-400 rounded-lg cursor-not-allowed">
            Current Plan
          </button>
        ) : (
          <button onClick={() => handlePlanChange(tier.id)} className="w-full py-3 bg-primary-600 text-white rounded-lg">
            {getTierLevel(tier.id) > getTierLevel(user?.subscription_tier) ? 'Upgrade' : 'Switch'}
          </button>
        )}
      </div>
    </div>
  )
})}
```

**SparkleEffect component:**

```tsx
function SparkleEffect() {
  const containerRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    if (!containerRef.current) return
    
    const container = containerRef.current
    const interval = setInterval(() => {
      const sparkle = document.createElement('div')
      const x = Math.random() * container.offsetWidth
      const size = 4 + Math.random() * 4
      
      sparkle.style.cssText = `
        position: absolute;
        left: ${x}px;
        bottom: 0;
        width: ${size}px;
        height: ${size}px;
        background: radial-gradient(circle, #ffd700, transparent);
        border-radius: 50%;
        pointer-events: none;
        animation: sparkle-rise 3s ease-out forwards;
        box-shadow: 0 0 ${size}px #ffd700;
      `
      
      container.appendChild(sparkle)
      setTimeout(() => sparkle.remove(), 3000)
    }, 150)
    
    return () => clearInterval(interval)
  }, [])
  
  return (
    <div ref={containerRef} className="absolute inset-0 overflow-visible pointer-events-none z-10">
      <style jsx global>{`
        @keyframes sparkle-rise {
          0% { transform: translateY(0) scale(1); opacity: 1; }
          100% { transform: translateY(-150px) scale(0); opacity: 0; }
        }
      `}</style>
    </div>
  )
}
```

---

### ISSUE 5: "Start Free Trial" Button Should NOT Show for Existing Subscribers

**Current:** All plans show "Start Free Trial" button
**Wanted:** Button text/action changes based on user state

**Logic:**

```tsx
// Determine button state
const userTier = user?.subscription_tier?.toUpperCase()
const userStatus = user?.subscription_status?.toUpperCase()
const isOnTrial = userStatus === 'TRIALING'
const isPaying = userStatus === 'ACTIVE' && !isOnTrial
const isCurrentPlan = userTier === tier.id.toUpperCase()
const hasHadTrial = user?.trial_start != null  // User already used their trial

// Button rendering
{isCurrentPlan ? (
  <button disabled className="bg-gray-100 text-gray-400 cursor-not-allowed">
    Current Plan
  </button>
) : isOnTrial ? (
  // ON TRIAL - can switch plans, trial continues
  <button onClick={() => handlePlanSwitch(tier.id)} className="bg-primary-600 text-white">
    Switch to {tier.name}
  </button>
) : isPaying ? (
  // PAYING - upgrade/downgrade
  <button onClick={() => handlePlanChange(tier.id)} className="bg-primary-600 text-white">
    {getTierLevel(tier.id) > getTierLevel(userTier) ? 'Upgrade' : 'Downgrade'} to {tier.name}
  </button>
) : hasHadTrial ? (
  // USED TRIAL BEFORE - no more free trial
  <button onClick={() => handleSubscribe(tier.id)} className="bg-primary-600 text-white">
    Subscribe to {tier.name}
  </button>
) : (
  // NEW USER - can start trial
  <button onClick={() => handleStartTrial(tier.id)} className="bg-primary-600 text-white">
    Start Free Trial
  </button>
)}
```

---

## FILES TO MODIFY

### Frontend:

1. **`frontend/src/components/MarketCard.tsx`** - Create/update with:
   - Overlapping circular image at top
   - Diagonal footer with platform logo and brand color
   - Use `/logos/kalshi-logo.png` and `/logos/polymarket-logo.png`

2. **`frontend/src/components/Sidebar.tsx`** - Update bottom section:
   - Show trial countdown if `subscription_status === 'TRIALING'`
   - Show tier badge if paid (`subscription_status === 'ACTIVE'`)
   - Only show "Start free trial" if no subscription

3. **`frontend/src/app/(app)/settings/page.tsx`** - Update plan cards:
   - Add SparkleEffect component for current plan
   - Add "YOU" badge on current plan
   - Gold border + glow on current plan
   - Conditional button text (not "Start Free Trial" for existing subscribers)

4. **`frontend/src/components/SparkleEffect.tsx`** - Create sparkle animation component

### Backend:

5. **`app/services/kalshi_client.py`** - Extract `image_url` from market/event data

6. **`app/services/polymarket_client.py`** - Extract `image` from event data

7. **`app/models/market.py`** - Add `image_url` column if not exists

---

## PLATFORM COLORS REFERENCE

```typescript
const PLATFORMS = {
  kalshi: {
    color: '#00D26A',      // Mint green
    logo: '/logos/kalshi-logo.png',
  },
  polymarket: {
    color: '#6366F1',      // Deep indigo/blue
    logo: '/logos/polymarket-logo.png',
  },
}
```

---

## VISUAL REFERENCE

**Card Layout:**
```
              ┌──────┐
              │ IMG  │  ← Circular image, overlaps top by 50%
         ┌────┴──────┴────┐
         │                │
         │  Market Title  │
         │                │
         │  Yes: 65%      │
         │  ████████░░    │
         │                │
         ├────────────────┤
         │[🟢]    ▓▓▓▓▓▓▓▓│  ← Logo left, diagonal color fill right
         └────────────────┘
```

**Diagonal Footer (using clip-path):**
```
┌────────────────────────────────┐
│ [LOGO] Kalshi      ████████████│  ← White left, green diagonal right
└────────────────────────────────┘
                     ↑
              clip-path: polygon(40% 0, 100% 0, 100% 100%, 20% 100%)
```
