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

// Centered logo watermark for cards
function CardWatermark() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <Image
        src="/oddwons-logo.png"
        alt=""
        width={64}
        height={64}
        className="rounded-lg opacity-[0.06]"
      />
    </div>
  )
}

export function StatsCard({ title, value, subtitle, icon: Icon, trend, color = 'blue' }: StatsCardProps) {
  return (
    <div className="card relative overflow-hidden">
      <CardWatermark />
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
