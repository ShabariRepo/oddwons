'use client'

import Image from 'next/image'
import { PLATFORMS, PlatformKey } from '@/lib/platforms'

interface MarketCardProps {
  market: {
    id: string
    title: string
    category?: string
    volume?: number
    yes_price?: number
    no_price?: number
    image_url?: string
    platform: 'kalshi' | 'polymarket'
  }
  onClick?: () => void
}

export default function MarketCard({ market, onClick }: MarketCardProps) {
  const platform = PLATFORMS[market.platform as PlatformKey]
  const yesPercent = market.yes_price ? Math.round(market.yes_price * 100) : 50

  const formatVolume = (vol: number) => {
    if (vol >= 1000000) return `$${(vol / 1000000).toFixed(1)}M`
    if (vol >= 1000) return `$${(vol / 1000).toFixed(0)}K`
    return `$${vol.toFixed(0)}`
  }

  // Fallback gradient colors for circular image placeholder
  const fallbackColors = {
    kalshi: 'from-green-400 to-emerald-600',
    polymarket: 'from-indigo-400 to-purple-600',
  }

  return (
    <div
      onClick={onClick}
      className="relative bg-white rounded-xl overflow-visible shadow-sm hover:shadow-lg transition-all cursor-pointer border border-gray-100 pt-10 mt-8"
    >
      {/* Floating Circular Image */}
      <div className="absolute -top-8 left-1/2 -translate-x-1/2 z-10">
        <div className="w-16 h-16 rounded-full overflow-hidden border-4 border-white shadow-lg">
          {market.image_url ? (
            <Image
              src={market.image_url}
              alt={market.title}
              width={64}
              height={64}
              className="object-cover w-full h-full"
              unoptimized
            />
          ) : (
            <div className={`w-full h-full bg-gradient-to-br ${fallbackColors[market.platform]}`} />
          )}
        </div>
      </div>

      {/* Card Body */}
      <div className="px-4 pb-4">
        {/* Category badge */}
        {market.category && (
          <div className="flex justify-center mb-2">
            <span className="px-2 py-0.5 bg-gray-100 rounded-full text-xs font-medium text-gray-600">
              {market.category}
            </span>
          </div>
        )}

        <h3 className="font-semibold text-gray-900 text-center line-clamp-2 mb-2">
          {market.title}
        </h3>

        {market.volume !== undefined && market.volume > 0 && (
          <p className="text-sm text-gray-500 text-center mb-3">
            Volume: {formatVolume(market.volume)}
          </p>
        )}

        {/* Price bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-green-600 font-medium">Yes {yesPercent}%</span>
            <span className="text-red-500 font-medium">No {100 - yesPercent}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
            <div
              className="bg-green-500 transition-all"
              style={{ width: `${yesPercent}%` }}
            />
            <div
              className="bg-red-400 transition-all"
              style={{ width: `${100 - yesPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Diagonal Gradient Footer */}
      <div className="relative h-12 overflow-hidden">
        {/* Diagonal background */}
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, white 0%, white 40%, ${platform.color} 40%, ${platform.color} 100%)`,
          }}
        />

        {/* Platform logo on left */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
          <Image
            src={platform.logo}
            alt={platform.name}
            width={24}
            height={24}
            className="object-contain"
          />
          <span className="text-sm font-medium text-gray-700">{platform.name}</span>
        </div>
      </div>
    </div>
  )
}
