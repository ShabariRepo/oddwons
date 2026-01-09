'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  TrendingUp,
  Bell,
  BarChart3,
  Settings,
  Sparkles,
  Scale,
  Shield,
} from 'lucide-react'
import { useAuth } from './AuthProvider'
import TierBadge from './TierBadge'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'AI Highlights', href: '/opportunities', icon: Sparkles },
  { name: 'Cross-Platform', href: '/cross-platform', icon: Scale },
  { name: 'Markets', href: '/markets', icon: TrendingUp },
  { name: 'Alerts', href: '/alerts', icon: Bell },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const tierColors: Record<string, string> = {
  basic: 'from-primary-600 to-primary-500',
  premium: 'from-purple-600 to-purple-500',
  pro: 'from-yellow-600 to-yellow-500',
}

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()

  const tier = user?.subscription_tier
  const hasSubscription = tier && user?.subscription_status === 'active'
  const tierLabel = tier ? tier.charAt(0).toUpperCase() + tier.slice(1) : 'No Plan'

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-gray-900">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-gray-800">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/oddwons-logo.png"
            alt="OddWons"
            width={32}
            height={32}
            className="rounded-lg"
          />
          <span className="text-xl font-bold text-white">OddWons</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          )
        })}

        {/* Admin Link - only visible to admins */}
        {user?.is_admin && (
          <Link
            href="/admin"
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mt-4 border-t border-gray-800 pt-4',
              pathname.startsWith('/admin')
                ? 'bg-amber-600 text-white'
                : 'text-amber-400 hover:text-white hover:bg-gray-800'
            )}
          >
            <Shield className="w-5 h-5" />
            Admin
          </Link>
        )}
      </nav>

      {/* Tier Badge */}
      <div className="p-4 border-t border-gray-800">
        {(() => {
          const isTrialing = user?.subscription_status === 'trialing'
          const isActive = user?.subscription_status === 'active'
          const hasTier = !!tier

          // Calculate days left for trial
          const daysLeft = user?.trial_end_date
            ? Math.max(0, Math.ceil((new Date(user.trial_end_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
            : 0

          if (isTrialing && hasTier && daysLeft > 0) {
            // On trial - show "X days left on trial"
            return (
              <TierBadge
                tier={tier.toUpperCase() as 'BASIC' | 'PREMIUM' | 'PRO'}
                daysLeft={daysLeft}
              />
            )
          } else if (isActive && hasTier) {
            // Paid active user - show tier ribbon badge
            return (
              <TierBadge tier={tier.toUpperCase() as 'BASIC' | 'PREMIUM' | 'PRO'} />
            )
          } else {
            // No subscription - show "Start free trial"
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
      </div>
    </aside>
  )
}
