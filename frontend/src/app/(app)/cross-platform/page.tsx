'use client'

import { useState } from 'react'
import { Scale, TrendingUp, TrendingDown, ArrowRight, ExternalLink } from 'lucide-react'
import { useCrossPlatformMatches, useCrossPlatformStats } from '@/hooks/useAPI'
import { CrossPlatformMatch } from '@/lib/types'
import { clsx } from 'clsx'
import Image from 'next/image'
import GameCard from '@/components/GameCard'
import { PLATFORMS } from '@/lib/platforms'

function MatchCard({ match }: { match: CrossPlatformMatch }) {
  const kalshiPercent = match.kalshi_yes_price ? Math.round(match.kalshi_yes_price) : 50
  const polyPercent = match.polymarket_yes_price ? Math.round(match.polymarket_yes_price) : 50
  const gapColor = Math.abs(match.price_gap_cents) >= 5 ? 'text-green-600' : 'text-yellow-600'

  // Construct Kalshi URL from market ID (e.g., "kalshi_FED-26JAN29" -> "FED")
  const kalshiUrl = match.kalshi_market_id
    ? `https://kalshi.com/events/${match.kalshi_market_id.replace('kalshi_', '').split('-')[0]}`
    : null

  const handleCardClick = () => {
    if (kalshiUrl) {
      window.open(kalshiUrl, '_blank')
    }
  }

  return (
    <div className="relative pt-10 mt-8" onClick={handleCardClick}>
      {/* Floating Circle - Both logos for cross-platform */}
      <div className="absolute -top-2 left-1/2 -translate-x-1/2 z-20">
        <div className="w-20 h-20 rounded-full overflow-hidden border-4 border-white shadow-xl bg-gradient-to-br from-green-400 via-blue-500 to-purple-600">
          <div className="w-full h-full flex items-center justify-center">
            <div className="flex items-center -space-x-2">
              <Image src="/logos/kalshi-logo.png" alt="K" width={28} height={28} className="rounded-full border-2 border-white bg-white" />
              <Image src="/logos/polymarket-logo.png" alt="P" width={28} height={28} className="rounded-full border-2 border-white bg-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Card */}
      <GameCard className="bg-white rounded-xl shadow-sm cursor-pointer border border-gray-100 overflow-hidden" showWatermark={false}>
        <div className="px-4 pt-12 pb-4">
          {/* Category + Gap */}
          <div className="flex items-center justify-between mb-2">
            {match.category && (
              <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                {match.category}
              </span>
            )}
            <span className={`text-sm font-bold ${gapColor}`}>
              {match.price_gap_cents.toFixed(1)}¢ gap
            </span>
          </div>

          {/* Topic */}
          <h3 className="font-semibold text-gray-900 text-center mb-3 line-clamp-2">
            {match.topic}
          </h3>

          {/* Platform price boxes */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-green-50 rounded-lg py-2 px-3 text-center border border-green-100">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Image src="/logos/kalshi-logo.png" alt="K" width={14} height={14} />
                <span className="text-xs text-green-700 font-medium">Kalshi</span>
              </div>
              <p className="text-2xl font-bold text-green-700">{kalshiPercent}%</p>
            </div>
            <div className="bg-indigo-50 rounded-lg py-2 px-3 text-center border border-indigo-100">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Image src="/logos/polymarket-logo.png" alt="P" width={14} height={14} />
                <span className="text-xs text-indigo-700 font-medium">Polymarket</span>
              </div>
              <p className="text-2xl font-bold text-indigo-700">{polyPercent}%</p>
            </div>
          </div>

          {/* Volume */}
          <p className="text-sm text-gray-500 text-center">
            ${(match.combined_volume / 1000).toFixed(0)}K combined
          </p>
        </div>

        {/* Diagonal Footer - Split colors with platform links */}
        <div className="relative h-12 overflow-hidden">
          <div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(115deg, #00D26A 0%, #00D26A 50%, #6366F1 50%, #6366F1 100%)',
            }}
          />
          <div className="absolute inset-0 flex items-center justify-between px-4 z-10">
            {kalshiUrl && (
              <a
                href={kalshiUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-white text-xs font-medium hover:underline flex items-center gap-1"
              >
                Trade on Kalshi <ExternalLink className="w-3 h-3" />
              </a>
            )}
            {match.polymarket_market_id && (
              <a
                href="https://polymarket.com"
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-white text-xs font-medium hover:underline flex items-center gap-1"
              >
                Trade on Polymarket <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      </GameCard>
    </div>
  )
}

function MatchCardSkeleton() {
  return (
    <div className="relative pt-10 mt-8">
      <div className="absolute -top-2 left-1/2 -translate-x-1/2 z-20">
        <div className="w-20 h-20 rounded-full bg-gray-200 animate-pulse border-4 border-white shadow-xl" />
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-4 pt-12 pb-4 space-y-3">
          <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
          <div className="grid grid-cols-2 gap-3">
            <div className="h-16 bg-gray-200 rounded animate-pulse" />
            <div className="h-16 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <div className="h-10 bg-gray-100" />
      </div>
    </div>
  )
}

export default function CrossPlatformPage() {
  const [minGap, setMinGap] = useState<number | null>(null)
  const { data, isLoading, error } = useCrossPlatformMatches({ limit: 50 })
  const { data: stats } = useCrossPlatformStats()

  const filteredMatches = minGap
    ? data?.matches?.filter(m => Math.abs(m.price_gap_cents) >= minGap)
    : data?.matches

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Scale className="w-6 h-6 text-primary-500" />
          <h1 className="text-2xl font-bold text-gray-900">Cross-Platform Watch</h1>
        </div>
        <p className="text-gray-500">
          Compare the same prediction markets across Kalshi and Polymarket
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Matches</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total_matches || data?.total || 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Combined Volume</p>
          <p className="text-2xl font-bold text-gray-900">
            ${((stats?.total_volume || data?.total_volume || 0) / 1000000).toFixed(1)}M
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Avg Price Gap</p>
          <p className="text-2xl font-bold text-gray-900">
            {stats?.avg_price_gap?.toFixed(1) || '0'}¢
          </p>
        </div>
      </div>

      {/* Filter */}
      <div className="card">
        <p className="text-sm font-medium text-gray-700 mb-3">Filter by minimum gap</p>
        <div className="flex flex-wrap gap-2">
          {[null, 1, 2, 3, 5, 10].map((gap) => (
            <button
              key={gap ?? 'all'}
              onClick={() => setMinGap(gap)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                minGap === gap
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {gap === null ? 'All' : `≥${gap}¢`}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <p className="text-sm text-gray-600">
        Showing {filteredMatches?.length || 0} cross-platform matches
      </p>

      {/* Matches Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <MatchCardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-12">
          <p className="text-red-500">Failed to load matches</p>
        </div>
      ) : filteredMatches?.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredMatches.map((match) => (
            <MatchCard key={match.match_id} match={match} />
          ))}
        </div>
      ) : (
        <div className="card text-center py-16">
          <Scale className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No cross-platform matches found</h3>
          <p className="text-gray-500 mt-2 max-w-md mx-auto">
            Cross-platform matches will appear here when the same markets are found on both Kalshi and Polymarket.
          </p>
        </div>
      )}

      {/* Info Card */}
      <div className="card bg-gray-50">
        <h3 className="font-semibold text-gray-900 mb-2">About Cross-Platform Matching</h3>
        <p className="text-sm text-gray-600">
          We use fuzzy matching to find the same prediction markets across different platforms.
          Price gaps may indicate different market sentiment, liquidity differences, or trading opportunities.
          Always verify the exact market terms before trading.
        </p>
      </div>
    </div>
  )
}
