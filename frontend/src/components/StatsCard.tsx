import { clsx } from 'clsx'
import { LucideIcon } from 'lucide-react'
import Image from 'next/image'

interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: {
    value: number
    isPositive: boolean
  }
  color?: 'blue' | 'green' | 'purple' | 'orange'
}

const colorClasses = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-green-50 text-green-600',
  purple: 'bg-purple-50 text-purple-600',
  orange: 'bg-orange-50 text-orange-600',
}

// Mini brand pattern for card backgrounds
function CardBrandPattern() {
  const items = [
    { type: 'logo', x: 75, y: 60, rotate: 15, size: 24 },
    { type: 'cash', x: 85, y: 20, rotate: -10, size: 18 },
    { type: 'smile', x: 65, y: 85, rotate: 8, size: 16 },
    { type: 'logo', x: 90, y: 75, rotate: -5, size: 20 },
  ]

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {items.map((item, i) => (
        <div
          key={i}
          className="absolute select-none opacity-[0.06]"
          style={{
            left: `${item.x}%`,
            top: `${item.y}%`,
            transform: `rotate(${item.rotate}deg)`,
          }}
        >
          {item.type === 'logo' ? (
            <Image
              src="/oddwons-logo.png"
              alt=""
              width={item.size}
              height={item.size}
              className="rounded"
            />
          ) : (
            <span style={{ fontSize: `${item.size}px` }}>
              {item.type === 'cash' ? '💸' : '😁'}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}

export function StatsCard({ title, value, subtitle, icon: Icon, trend, color = 'blue' }: StatsCardProps) {
  return (
    <div className="card relative overflow-hidden">
      <CardBrandPattern />
      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend && (
            <div className={clsx(
              'flex items-center gap-1 mt-2 text-sm font-medium',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              <span>{trend.isPositive ? '+' : ''}{trend.value}%</span>
              <span className="text-gray-400">vs last hour</span>
            </div>
          )}
        </div>
        <div className={clsx('p-3 rounded-lg', colorClasses[color])}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}

export function StatsCardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-start justify-between">
        <div>
          <div className="h-4 w-24 bg-gray-200 rounded"></div>
          <div className="h-8 w-16 bg-gray-200 rounded mt-2"></div>
        </div>
        <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
      </div>
    </div>
  )
}
