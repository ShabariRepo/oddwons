'use client'

import Link from 'next/link'
import { useAuth } from './AuthProvider'

const TIER_CONFIG = {
  free: {
    bg: 'bg-gradient-to-r from-gray-700 to-gray-900',
    message: "FREE tier | 3 highlights daily | Upgrade for full insights",
    showUpgrade: true,
  },
  basic: {
    bg: 'bg-gradient-to-r from-blue-600 to-blue-800',
    message: "BASIC tier | 10 highlights | Upgrade for analyst notes",
    showUpgrade: true,
  },
  premium: {
    bg: 'bg-gradient-to-r from-purple-600 to-purple-800',
    message: "PREMIUM | Full context unlocked | Go PRO for real-time",
    showUpgrade: true,
  },
  pro: {
    bg: 'bg-gradient-to-r from-amber-500 to-orange-600',
    message: "PRO | All features unlocked | You're him",
    showUpgrade: false,
  },
}

export function TierBanner() {
  const { user } = useAuth()

  const tierKey = (user?.subscription_tier?.toLowerCase() || 'free') as keyof typeof TIER_CONFIG
  const config = TIER_CONFIG[tierKey] || TIER_CONFIG.free

  return (
    <div className={`${config.bg} text-white overflow-hidden relative`}>
      <div className="flex animate-marquee whitespace-nowrap py-1.5">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="flex items-center mx-8">
            <span className="animate-wiggle inline-block mr-3 text-base">🐛</span>
            <span className="text-sm font-medium tracking-wide">{config.message}</span>
          </div>
        ))}
      </div>

      {config.showUpgrade && (
        <div className="absolute right-0 top-0 bottom-0 flex items-center bg-gradient-to-l from-black/50 to-transparent pl-16 pr-4">
          <Link
            href="/settings"
            className="text-xs font-bold bg-white/20 hover:bg-white/30 px-3 py-1 rounded-full transition-all hover:scale-105"
          >
            Upgrade
          </Link>
        </div>
      )}
    </div>
  )
}

export default TierBanner
