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
  Zap,
} from 'lucide-react'
import { useAuth } from './AuthProvider'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Opportunities', href: '/opportunities', icon: Zap },
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
      </nav>

      {/* Tier Badge */}
      <div className="p-4 border-t border-gray-800">
        {hasSubscription ? (
          <div className={clsx('bg-gradient-to-r rounded-lg p-4', tierColors[tier!])}>
            <p className="text-xs text-white/80 uppercase tracking-wide">Current Plan</p>
            <p className="text-lg font-bold text-white mt-1">{tierLabel}</p>
            {tier !== 'pro' && (
              <Link
                href="/settings"
                className="mt-3 block text-center text-sm text-white bg-white/20 hover:bg-white/30 rounded-lg py-2 transition-colors"
              >
                Manage Plan
              </Link>
            )}
          </div>
        ) : (
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
        )}
      </div>
    </aside>
  )
}
