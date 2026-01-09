'use client'

import { useState } from 'react'
import { Sparkles, Filter, RefreshCw } from 'lucide-react'
import { useAIInsights } from '@/hooks/useAPI'
import { AIInsight } from '@/lib/types'
import { clsx } from 'clsx'
import Link from 'next/link'
import Image from 'next/image'
import GameCard from '@/components/GameCard'

const categories = [
  { id: '', name: 'All Categories' },
  { id: 'politics', name: 'Politics' },
  { id: 'sports', name: 'Sports' },
  { id: 'crypto', name: 'Crypto' },
  { id: 'finance', name: 'Finance' },
  { id: 'tech', name: 'Tech' },
  { id: 'entertainment', name: 'Entertainment' },
]

function InsightCard({ insight }: { insight: AIInsight }) {
  // Platform colors
  const platformConfig = {
    kalshi: {
      color: '#00D26A',
      logo: '/logos/kalshi-logo.png',
      gradient: 'from-green-400 to-emerald-600',
    },
    polymarket: {
      color: '#6366F1',
      logo: '/logos/polymarket-logo.png',
      gradient: 'from-indigo-400 to-purple-600',
    },
  }

  const platform = platformConfig[insight.platform as keyof typeof platformConfig] || platformConfig.polymarket

  const movementColor = insight.recent_movement?.includes('+')
    ? 'text-green-600'
    : insight.recent_movement?.includes('-')
    ? 'text-red-600'
    : 'text-gray-500'

  return (
    <Link href={`/insights/${insight.id}`}>
      {/* Container with padding for floating image */}
      <div className="relative pt-10 mt-8">

        {/* Floating Circular Image - ~50% overlaps the card */}
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 z-30">
          <div className={`w-20 h-20 rounded-full overflow-hidden border-4 border-white shadow-xl bg-gradient-to-br ${platform.gradient}`}>
            {insight.image_url ? (
              <Image
                src={insight.image_url}
                alt=""
                width={80}
                height={80}
                className="object-cover w-full h-full"
                unoptimized
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white text-2xl font-bold">
                {insight.market_title?.charAt(0) || '?'}
              </div>
            )}
          </div>
        </div>

        {/* Card with hover effects */}
        <GameCard className="bg-white rounded-xl shadow-sm cursor-pointer border border-gray-100 overflow-hidden" showWatermark={false}>

          {/* Card Body */}
          <div className="px-4 pt-12 pb-4">
            {/* Category Badge - centered */}
            <div className="flex justify-center mb-2">
              {insight.category && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                  {insight.category}
                </span>
              )}
            </div>

            {/* Title */}
            <h3 className="font-semibold text-gray-900 text-center mb-2 line-clamp-2">
              {insight.market_title}
            </h3>

            {/* Summary */}
            <p className="text-sm text-gray-600 mb-4 line-clamp-3 text-center">
              {insight.summary}
            </p>

            {/* Odds */}
            {insight.current_odds && (
              <div className="flex items-center gap-4 mb-3">
                <div className="flex-1 bg-green-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-green-600">Yes</p>
                  <p className="text-lg font-bold text-green-700">
                    {(insight.current_odds.yes * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="flex-1 bg-red-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-red-600">No</p>
                  <p className="text-lg font-bold text-red-700">
                    {(insight.current_odds.no * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            )}

            {/* Movement */}
            {insight.recent_movement && (
              <div className={`text-center text-sm font-medium ${movementColor} mb-2`}>
                {insight.recent_movement}
              </div>
            )}

            {/* Volume Note */}
            {insight.volume_note && (
              <p className="text-xs text-gray-500 text-center">{insight.volume_note}</p>
            )}
          </div>

          {/* DIAGONAL FOOTER WITH PLATFORM LOGO */}
          <div className="relative h-12 overflow-hidden">
            {/* Diagonal gradient background */}
            <div
              className="absolute inset-0"
              style={{
                background: `linear-gradient(115deg, white 0%, white 40%, ${platform.color} 40%, ${platform.color} 100%)`,
              }}
            />

            {/* Platform logo and name on left */}
            <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2 z-10">
              <Image
                src={platform.logo}
                alt={insight.platform}
                width={20}
                height={20}
                className="object-contain"
              />
              <span className="text-sm font-medium text-gray-700 capitalize">
                {insight.platform}
              </span>
            </div>
          </div>
        </GameCard>
      </div>
    </Link>
  )
}

function InsightCardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex gap-2 mb-3">
        <div className="h-5 w-16 bg-gray-200 rounded" />
        <div className="h-5 w-20 bg-gray-200 rounded" />
      </div>
      <div className="h-6 w-full bg-gray-200 rounded mb-2" />
      <div className="h-4 w-3/4 bg-gray-200 rounded mb-4" />
      <div className="h-16 w-full bg-gray-200 rounded mb-3" />
      <div className="flex gap-4 mb-3">
        <div className="flex-1 h-16 bg-gray-200 rounded" />
        <div className="flex-1 h-16 bg-gray-200 rounded" />
      </div>
      <div className="h-4 w-1/2 bg-gray-200 rounded" />
    </div>
  )
}

export default function OpportunitiesPage() {
  const [selectedCategory, setSelectedCategory] = useState('')
  const { data, isLoading, error, mutate } = useAIInsights({
    category: selectedCategory || undefined,
    limit: 30,
  })

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-primary-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Market Highlights</h1>
            <p className="text-gray-500 mt-1">
              AI-powered insights across prediction markets
            </p>
          </div>
        </div>

        <button
          onClick={() => mutate()}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Tier Info */}
      {data && (
        <div className="card bg-gradient-to-r from-primary-50 to-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">
                {data.tier.toUpperCase()} Tier
              </p>
              <p className="text-xs text-gray-500">
                {data.count} highlights • Refreshes {data.refresh}
              </p>
            </div>
            {data.upgrade_prompt && (
              <a href="/settings" className="btn-primary text-sm">
                Upgrade
              </a>
            )}
          </div>
          {data.upgrade_prompt && (
            <p className="text-sm text-primary-700 mt-2">{data.upgrade_prompt}</p>
          )}
        </div>
      )}

      {/* Category Filter */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filter by Category</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedCategory === cat.id
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* Results Count */}
      <p className="text-sm text-gray-600">
        {data?.count || 0} market highlights
        {selectedCategory && ` in ${selectedCategory}`}
      </p>

      {/* Insights Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <InsightCardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-12">
          <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Sign in to view highlights</h3>
          <p className="text-gray-500 mt-2">
            AI market highlights are available to registered users
          </p>
          <a href="/login" className="btn-primary mt-4 inline-block">
            Sign In
          </a>
        </div>
      ) : data?.insights?.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data.insights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      ) : (
        <div className="card text-center py-16">
          <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No highlights found</h3>
          <p className="text-gray-500 mt-2 max-w-md mx-auto">
            {selectedCategory
              ? `No highlights in ${selectedCategory} category. Try selecting a different category.`
              : 'Market highlights will appear here once AI analysis runs.'}
          </p>
        </div>
      )}
    </div>
  )
}
