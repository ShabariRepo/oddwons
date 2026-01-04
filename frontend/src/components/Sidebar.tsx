'use client'

import Link from 'next/link'
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
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Opportunities', href: '/opportunities', icon: Zap },
  { name: 'Markets', href: '/markets', icon: TrendingUp },
  { name: 'Alerts', href: '/alerts', icon: Bell },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const tierColors: Record<string, string> = {
  free: 'from-gray-600 to-gray-500',
  basic: 'from-primary-600 to-primary-500',
  premium: 'from-purple-600 to-purple-500',
  pro: 'from-yellow-600 to-yellow-500',
}

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()

  const tier = user?.subscription_tier || 'free'
  const tierLabel = tier.charAt(0).toUpperCase() + tier.slice(1)

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-gray-900">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-gray-800">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
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
        <div className={clsx('bg-gradient-to-r rounded-lg p-4', tierColors[tier])}>
          <p className="text-xs text-white/80 uppercase tracking-wide">Current Plan</p>
          <p className="text-lg font-bold text-white mt-1">{tierLabel}</p>
          {tier === 'free' && (
            <Link
              href="/settings"
              className="mt-3 block text-center text-sm text-white bg-white/20 hover:bg-white/30 rounded-lg py-2 transition-colors"
            >
              Upgrade Plan
            </Link>
          )}
          {tier !== 'free' && tier !== 'pro' && (
            <Link
              href="/settings"
              className="mt-3 block text-center text-sm text-white bg-white/20 hover:bg-white/30 rounded-lg py-2 transition-colors"
            >
              Manage Plan
            </Link>
          )}
        </div>
      </div>
    </aside>
  )
}
