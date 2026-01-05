'use client'

import { useState } from 'react'
import { Scale, TrendingUp, TrendingDown, ArrowRight, ExternalLink } from 'lucide-react'
import { useCrossPlatformMatches, useCrossPlatformStats } from '@/hooks/useAPI'
import { CrossPlatformMatch } from '@/lib/types'
import { clsx } from 'clsx'

function MatchCard({ match }: { match: CrossPlatformMatch }) {
  const gapColor = Math.abs(match.price_gap_cents) >= 5
    ? 'text-green-600 bg-green-50'
    : Math.abs(match.price_gap_cents) >= 2
    ? 'text-yellow-600 bg-yellow-50'
    : 'text-gray-600 bg-gray-50'

  const higherPlatform = match.gap_direction === 'kalshi_higher' ? 'Kalshi' : 'Polymarket'

  return (
    <div className="card hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-primary-500" />
          {match.category && (
            <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
              {match.category}
            </span>
          )}
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${gapColor}`}>
          {match.price_gap_cents.toFixed(1)}¢ gap
        </span>
      </div>

      {/* Topic */}
      <h3 className="font-medium text-gray-900 mb-4">
        {match.topic}
      </h3>

      {/* Price Comparison */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className={clsx(
          'rounded-lg p-3',
          match.gap_direction === 'kalshi_higher' ? 'bg-blue-100' : 'bg-blue-50'
        )}>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-blue-600 font-medium">Kalshi</p>
            {match.gap_direction === 'kalshi_higher' && (
              <TrendingUp className="w-3 h-3 text-blue-600" />
            )}
          </div>
          <p className="text-2xl font-bold text-blue-800">
            {match.kalshi_yes_price?.toFixed(0)}¢
          </p>
          <p className="text-xs text-blue-600 mt-1">
            ${((match.kalshi_volume || 0) / 1000).toFixed(0)}K volume
          </p>
        </div>

        <div className={clsx(
          'rounded-lg p-3',
          match.gap_direction === 'polymarket_higher' ? 'bg-purple-100' : 'bg-purple-50'
        )}>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-purple-600 font-medium">Polymarket</p>
            {match.gap_direction === 'polymarket_higher' && (
              <TrendingUp className="w-3 h-3 text-purple-600" />
            )}
          </div>
          <p className="text-2xl font-bold text-purple-800">
            {match.polymarket_yes_price?.toFixed(0)}¢
          </p>
          <p className="text-xs text-purple-600 mt-1">
            ${((match.polymarket_volume || 0) / 1000).toFixed(0)}K volume
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          <span className="font-medium">{higherPlatform}</span> priced higher
        </div>
        <div className="text-xs text-gray-500">
          ${(match.combined_volume / 1000).toFixed(0)}K combined
        </div>
      </div>

      {/* Match quality indicator */}
      {match.similarity_score && (
        <div className="mt-2 text-xs text-gray-400">
          {(match.similarity_score * 100).toFixed(0)}% match confidence
        </div>
      )}
    </div>
  )
}

function MatchCardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex justify-between mb-3">
        <div className="h-5 w-20 bg-gray-200 rounded" />
        <div className="h-5 w-16 bg-gray-200 rounded" />
      </div>
      <div className="h-6 w-full bg-gray-200 rounded mb-4" />
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="h-24 bg-gray-200 rounded" />
        <div className="h-24 bg-gray-200 rounded" />
      </div>
      <div className="h-4 w-full bg-gray-200 rounded" />
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
