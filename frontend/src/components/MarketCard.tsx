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

  // Fallback gradient if no image
  const fallbackGradients = {
    kalshi: 'from-green-400 via-emerald-500 to-teal-600',
    polymarket: 'from-purple-400 via-violet-500 to-indigo-600',
  }

  const formatVolume = (vol: number) => {
    if (vol >= 1000000) return `$${(vol / 1000000).toFixed(1)}M`
    if (vol >= 1000) return `$${(vol / 1000).toFixed(0)}K`
    return `$${vol.toFixed(0)}`
  }

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all cursor-pointer border border-gray-100"
    >
      {/* Image Header */}
      <div className="relative h-32 overflow-hidden">
        {market.image_url ? (
          <Image
            src={market.image_url}
            alt={market.title}
            fill
            className="object-cover"
            unoptimized
          />
        ) : (
          <div className={`absolute inset-0 bg-gradient-to-br ${fallbackGradients[market.platform]}`} />
        )}

        {/* Gradient overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

        {/* Category badge */}
        {market.category && (
          <span className="absolute top-3 left-3 px-2 py-1 bg-white/90 backdrop-blur-sm rounded-full text-xs font-medium text-gray-700">
            {market.category}
          </span>
        )}
      </div>

      {/* Card Body */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2">
          {market.title}
        </h3>

        {market.volume !== undefined && market.volume > 0 && (
          <p className="text-sm text-gray-500 mb-3">
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

      {/* Platform Footer */}
      <div className="flex items-center border-t border-gray-100">
        {/* Logo section - left */}
        <div className="flex items-center gap-2 px-4 py-2">
          <Image
            src={platform.logo}
            alt={platform.name}
            width={20}
            height={20}
            className="object-contain"
          />
          <span className="text-sm font-medium text-gray-700">{platform.name}</span>
        </div>

        {/* Brand color fill - right */}
        <div
          className="flex-1 h-full min-h-[36px]"
          style={{ backgroundColor: platform.color }}
        />
      </div>
    </div>
  )
}
