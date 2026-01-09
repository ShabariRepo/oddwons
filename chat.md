# OddWons - EXPLICIT FIX INSTRUCTIONS

**CRITICAL: The opportunities page uses `InsightCard` (inline component), NOT `MarketCard`. You must update `InsightCard` in the opportunities page file itself.**

---

## PROBLEM 1: AI Highlights Cards Don't Have New Design

**File:** `frontend/src/app/(app)/opportunities/page.tsx`

**Issue:** The `InsightCard` component on lines 25-120 is an inline component that doesn't have:
- Floating circular image at top
- Diagonal platform footer with logo

**FIX:** Replace the entire `InsightCard` function (lines 25-120) with this:

```tsx
function InsightCard({ insight }: { insight: AIInsight }) {
  // Platform colors
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

  const movementColor = insight.recent_movement?.includes('+')
    ? 'text-green-600'
    : insight.recent_movement?.includes('-')
    ? 'text-red-600'
    : 'text-gray-500'

  return (
    <Link href={`/insights/${insight.id}`}>
      {/* Container with padding for floating image */}
      <div className="relative pt-10 mt-8">
        
        {/* Floating Circular Image */}
        <div className="absolute -top-6 left-1/2 -translate-x-1/2 z-20">
          <div className={`w-16 h-16 rounded-full overflow-hidden border-4 border-white shadow-lg bg-gradient-to-br ${platform.gradient}`}>
            {insight.image_url ? (
              <Image
                src={insight.image_url}
                alt=""
                width={64}
                height={64}
                className="object-cover w-full h-full"
                unoptimized
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white text-xl font-bold">
                {insight.market_title?.charAt(0) || '?'}
              </div>
            )}
          </div>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-shadow cursor-pointer border border-gray-100 overflow-hidden">
          
          {/* Card Body */}
          <div className="px-4 pt-8 pb-4">
            {/* Category Badge - centered */}
            <div className="flex justify-center mb-2">
              {insight.category && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                  {insight.category}
                </span>
              )}
            </div>

            {/* Title */}
            <h3 className="font-semibold text-gray-900 text-center mb-2 line-clamp-2">
              {insight.market_title}
            </h3>

            {/* Summary */}
            <p className="text-sm text-gray-600 mb-4 line-clamp-3 text-center">
              {insight.summary}
            </p>

            {/* Odds */}
            {insight.current_odds && (
              <div className="flex items-center gap-4 mb-3">
                <div className="flex-1 bg-green-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-green-600">Yes</p>
                  <p className="text-lg font-bold text-green-700">
                    {(insight.current_odds.yes * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="flex-1 bg-red-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-red-600">No</p>
                  <p className="text-lg font-bold text-red-700">
                    {(insight.current_odds.no * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            )}

            {/* Movement */}
            {insight.recent_movement && (
              <div className={`text-center text-sm font-medium ${movementColor} mb-2`}>
                {insight.recent_movement}
              </div>
            )}

            {/* Volume Note */}
            {insight.volume_note && (
              <p className="text-xs text-gray-500 text-center">{insight.volume_note}</p>
            )}
          </div>

          {/* DIAGONAL FOOTER WITH PLATFORM LOGO */}
          <div className="relative h-12 overflow-hidden">
            {/* Diagonal gradient background */}
            <div
              className="absolute inset-0"
              style={{
                background: `linear-gradient(115deg, white 0%, white 40%, ${platform.color} 40%, ${platform.color} 100%)`,
              }}
            />
            
            {/* Platform logo and name on left */}
            <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2 z-10">
              <Image
                src={platform.logo}
                alt={insight.platform}
                width={20}
                height={20}
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

**ALSO ADD this import at the top of the file (after existing imports):**

```tsx
import Image from 'next/image'
```

---

## PROBLEM 2: Sidebar Shows "NO ACTIVE PLAN" for Subscribed Users

**File:** `frontend/src/components/Sidebar.tsx`

**Issue:** The subscription_status comparison might be failing due to case sensitivity. The API returns uppercase ('TRIALING', 'ACTIVE') but code checks lowercase.

**FIX:** Find the tier badge section (around line 72) and replace the entire `{(() => {` block with:

```tsx
{(() => {
  // Normalize to lowercase for comparison
  const status = user?.subscription_status?.toLowerCase()
  const tier = user?.subscription_tier?.toLowerCase()
  
  const isTrialing = status === 'trialing'
  const isActive = status === 'active'
  const hasTier = !!tier && tier !== 'free'

  // Calculate days left for trial
  const trialEnd = user?.trial_end_date || user?.trial_end
  const daysLeft = trialEnd
    ? Math.max(0, Math.ceil((new Date(trialEnd).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
    : 0

  console.log('Sidebar Debug:', { status, tier, isTrialing, isActive, hasTier, daysLeft, trialEnd })

  if (isTrialing && hasTier && daysLeft > 0) {
    // On trial - show countdown
    return (
      <TierBadge
        tier={tier.toUpperCase() as 'BASIC' | 'PREMIUM' | 'PRO'}
        daysLeft={daysLeft}
      />
    )
  } else if (isActive && hasTier) {
    // Paid user - show tier badge
    return (
      <TierBadge tier={tier.toUpperCase() as 'BASIC' | 'PREMIUM' | 'PRO'} />
    )
  } else {
    // No subscription
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide">No Active Plan</p>
        <p className="text-sm text-gray-300 mt-1">Start your 7-day free trial</p>
        <Link
          href="/settings"
          className="mt-3 block text-center text-sm text-white bg-primary-600 hover:bg-primary-700 rounded-lg py-2 transition-colors"
        >
          🚀 Choose a Plan
        </Link>
      </div>
    )
  }
})()}
```

---

## PROBLEM 3: Settings Page - Current Plan Section Shows Wrong Info

**File:** `frontend/src/app/(app)/settings/page.tsx`

**Issue:** Same case sensitivity problem. Also "Current Plan" card shows wrong status.

**FIX 1:** Find the "Current Plan" card section (around line 130) and update the conditions:

```tsx
<div className="card">
  <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Plan</h2>
  <div className="flex items-center justify-between">
    <div className="flex items-center gap-4">
      <div className={clsx(
        'p-3 rounded-lg',
        (user?.subscription_status?.toLowerCase() === 'active' || user?.subscription_status?.toLowerCase() === 'trialing')
          ? 'bg-primary-100' 
          : 'bg-gray-100'
      )}>
        <CreditCard className={clsx(
          'w-6 h-6',
          (user?.subscription_status?.toLowerCase() === 'active' || user?.subscription_status?.toLowerCase() === 'trialing')
            ? 'text-primary-600' 
            : 'text-gray-400'
        )} />
      </div>
      <div>
        <p className="font-medium text-gray-900">
          {user?.subscription_tier
            ? `${user.subscription_tier.charAt(0).toUpperCase() + user.subscription_tier.slice(1)} Plan`
            : 'No Active Plan'}
        </p>
        <p className="text-sm text-gray-500">
          {user?.subscription_status?.toLowerCase() === 'trialing'
            ? `Free trial - ${Math.max(0, Math.ceil((new Date(user.trial_end_date || user.trial_end || '').getTime() - Date.now()) / (1000 * 60 * 60 * 24)))} days left`
            : user?.subscription_status?.toLowerCase() === 'active'
              ? 'Active subscription'
              : 'Start a 7-day free trial below'}
        </p>
      </div>
    </div>
    {(user?.subscription_status?.toLowerCase() === 'active' || user?.subscription_status?.toLowerCase() === 'trialing') && (
      <button
        onClick={handleManageSubscription}
        disabled={loading === 'portal'}
        className="btn-secondary flex items-center gap-2"
      >
        {loading === 'portal' && <Loader2 className="w-4 h-4 animate-spin" />}
        <ExternalLink className="w-4 h-4" />
        Manage Billing
      </button>
    )}
  </div>
</div>
```

**FIX 2:** In the plans.map section, update the conditions (around line 170):

```tsx
{plans.map((plan) => {
  // NORMALIZE TO LOWERCASE
  const userStatus = user?.subscription_status?.toLowerCase()
  const userTier = user?.subscription_tier?.toLowerCase()
  
  const isTrialing = userStatus === 'trialing'
  const isActive = userStatus === 'active'
  const isCurrent = (isActive || isTrialing) && plan.id.toLowerCase() === userTier
  const hasAnySubscription = isActive || isTrialing

  // ... rest of the code stays the same but uses these normalized variables
```

---

## PROBLEM 4: SparkleCard Animation Not Working

**File:** `frontend/src/components/SparkleCard.tsx`

**FIX:** Replace entire file with:

```tsx
'use client'

import { useEffect, useRef } from 'react'

interface SparkleCardProps {
  children: React.ReactNode
  active?: boolean
  className?: string
}

export default function SparkleCard({ children, active = false, className = '' }: SparkleCardProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!active || !containerRef.current) return

    const container = containerRef.current
    
    const createSparkle = () => {
      if (!container) return
      
      const sparkle = document.createElement('div')
      const x = Math.random() * container.offsetWidth
      const size = 4 + Math.random() * 6
      
      sparkle.style.cssText = `
        position: absolute;
        left: ${x}px;
        bottom: 0;
        width: ${size}px;
        height: ${size}px;
        background: radial-gradient(circle, #ffd700 0%, #ffec80 50%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 50;
        box-shadow: 0 0 ${size * 2}px #ffd700;
        animation: sparkle-float ${2 + Math.random() * 2}s ease-out forwards;
      `
      
      container.appendChild(sparkle)
      setTimeout(() => sparkle.remove(), 4000)
    }
    
    // Create initial sparkles
    for (let i = 0; i < 5; i++) {
      setTimeout(createSparkle, i * 200)
    }
    
    const interval = setInterval(createSparkle, 150)
    return () => clearInterval(interval)
  }, [active])

  return (
    <div
      ref={containerRef}
      className={`relative ${className}`}
      style={{ overflow: 'visible' }}
    >
      {children}
      
      <style jsx global>{`
        @keyframes sparkle-float {
          0% {
            transform: translateY(0) scale(1);
            opacity: 1;
          }
          100% {
            transform: translateY(-150px) scale(0);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}
```

---

## PROBLEM 5: Button Text Logic

**File:** `frontend/src/app/(app)/settings/page.tsx`

In the `getButtonText` function, make sure it uses normalized lowercase values:

```tsx
const getButtonText = () => {
  if (isCurrent) return 'Current Plan'
  if (!hasAnySubscription) return 'Start Free Trial'
  if (isTrialing) return `Switch to ${plan.name}`
  if (isUpgrade) return `Upgrade to ${plan.name}`
  return `Downgrade to ${plan.name}`
}
```

---

## VERIFICATION CHECKLIST

After making changes, verify in browser console:

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for "Sidebar Debug:" log
4. It should show: `{ status: 'trialing', tier: 'basic', isTrialing: true, ... }`

If `status` shows `'TRIALING'` (uppercase), that confirms the case sensitivity issue.

---

## FILES TO MODIFY (IN ORDER)

1. `frontend/src/components/SparkleCard.tsx` - Replace entire file
2. `frontend/src/components/Sidebar.tsx` - Fix tier badge logic (normalize case)
3. `frontend/src/app/(app)/settings/page.tsx` - Fix current plan + button logic (normalize case)
4. `frontend/src/app/(app)/opportunities/page.tsx` - Replace InsightCard with new design (add Image import)

---

## QUICK TEST

After deploying, the user (who has BASIC tier on trial) should see:
- **Sidebar:** "X days left on trial - BASIC plan" (not "NO ACTIVE PLAN")
- **Settings Current Plan:** "Basic Plan - Free trial - X days left" (not "No Active Plan")
- **Settings Plan Cards:** BASIC card should have gold border + sparkles + "YOU" badge
- **AI Highlights:** Cards should have circular image at top + diagonal colored footer
