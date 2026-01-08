'use client'

import { TrendingUp, Zap, BarChart3, Clock, ArrowRight, Sparkles, Scale } from 'lucide-react'
import { StatsCard, StatsCardSkeleton } from '@/components/StatsCard'
import { useMarketStats, usePatternStats, useAIInsights, useCrossPlatformMatches, useInsightStats } from '@/hooks/useAPI'
import { AIInsight, CrossPlatformMatch } from '@/lib/types'
import Link from 'next/link'
import BrandPattern from '@/components/BrandPattern'

function InsightCard({ insight }: { insight: AIInsight }) {
  const platformColor = insight.platform === 'kalshi'
    ? 'bg-blue-100 text-blue-800'
    : 'bg-purple-100 text-purple-800'

  return (
    <Link href={`/insights/${insight.id}`}>
    <div className="card hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${platformColor}`}>
          {insight.platform}
        </span>
        {insight.category && (
          <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
            {insight.category}
          </span>
        )}
      </div>

      <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">
        {insight.market_title}
      </h3>

      <p className="text-sm text-gray-600 line-clamp-3 mb-3">
        {insight.summary}
      </p>

      <div className="flex items-center justify-between text-sm">
        {insight.implied_probability && (
          <span className="text-primary-600 font-medium">
            {insight.implied_probability}
          </span>
        )}
        {insight.recent_movement && (
          <span className={`${
            insight.recent_movement.includes('+') ? 'text-green-600' :
            insight.recent_movement.includes('-') ? 'text-red-600' : 'text-gray-500'
          }`}>
            {insight.recent_movement}
          </span>
        )}
      </div>

      {insight.volume_note && (
        <p className="text-xs text-gray-500 mt-2">{insight.volume_note}</p>
      )}
    </div>
    </Link>
  )
}

function CrossPlatformCard({ match }: { match: CrossPlatformMatch }) {
  const gapColor = Math.abs(match.price_gap_cents) >= 3 ? 'text-green-600' : 'text-gray-600'

  return (
    <Link href={`/cross-platform`}>
    <div className="card hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-center gap-2 mb-3">
        <Scale className="w-4 h-4 text-primary-500" />
        <span className="text-xs font-medium text-primary-600 uppercase">Cross-Platform</span>
      </div>

      <h3 className="font-medium text-gray-900 line-clamp-2 mb-3">
        {match.topic}
      </h3>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-blue-50 rounded-lg p-2">
          <p className="text-xs text-blue-600 font-medium">Kalshi</p>
          <p className="text-lg font-bold text-blue-800">
            {match.kalshi_yes_price?.toFixed(0)}¢
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg p-2">
          <p className="text-xs text-purple-600 font-medium">Polymarket</p>
          <p className="text-lg font-bold text-purple-800">
            {match.polymarket_yes_price?.toFixed(0)}¢
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className={`text-sm font-medium ${gapColor}`}>
          {match.price_gap_cents.toFixed(1)}¢ gap
        </span>
        <span className="text-xs text-gray-500">
          ${(match.combined_volume / 1000).toFixed(0)}K vol
        </span>
      </div>
    </div>
    </Link>
  )
}

function InsightCardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex gap-2 mb-2">
        <div className="h-5 w-16 bg-gray-200 rounded" />
        <div className="h-5 w-20 bg-gray-200 rounded" />
      </div>
      <div className="h-5 w-full bg-gray-200 rounded mb-2" />
      <div className="h-4 w-3/4 bg-gray-200 rounded mb-3" />
      <div className="h-12 w-full bg-gray-200 rounded mb-3" />
      <div className="flex justify-between">
        <div className="h-4 w-20 bg-gray-200 rounded" />
        <div className="h-4 w-16 bg-gray-200 rounded" />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: marketStats, isLoading: statsLoading } = useMarketStats()
  const { data: patternStats } = usePatternStats()
  const { data: insightStats } = useInsightStats()
  const { data: aiInsights, isLoading: insightsLoading, error: insightsError } = useAIInsights({ limit: 6 })
  const { data: crossPlatform, isLoading: crossLoading } = useCrossPlatformMatches({ limit: 4 })

  const formatVolume = (vol: number) => {
    if (vol >= 1000000) return `$${(vol / 1000000).toFixed(1)}M`
    if (vol >= 1000) return `$${(vol / 1000).toFixed(0)}K`
    return `$${vol.toFixed(0)}`
  }

  const formatTime = (isoString?: string) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Your prediction market research companion</p>
      </div>

      {/* Stats Grid with Brand Pattern Background */}
      <div className="relative rounded-2xl overflow-hidden">
        <BrandPattern opacity={0.06} animated={false} />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 relative z-10 p-4 -m-4">
          {statsLoading ? (
            <>
              <StatsCardSkeleton />
              <StatsCardSkeleton />
              <StatsCardSkeleton />
              <StatsCardSkeleton />
            </>
          ) : (
            <>
              <StatsCard
                title="Markets Tracked"
                value={marketStats?.total_markets || 0}
                subtitle={`${marketStats?.kalshi_markets || 0} Kalshi, ${marketStats?.polymarket_markets || 0} Poly`}
                icon={TrendingUp}
                color="blue"
              />
              <StatsCard
                title="AI Highlights"
                value={insightStats?.active_highlights || patternStats?.active_patterns || 0}
                subtitle={`${insightStats?.categories_covered || 0} categories`}
                icon={Sparkles}
                color="purple"
              />
              <StatsCard
                title="Total Volume"
                value={formatVolume(marketStats?.total_volume || 0)}
                subtitle="Across all markets"
                icon={BarChart3}
                color="green"
              />
              <StatsCard
                title="Cross-Platform"
                value={crossPlatform?.total || 0}
                subtitle="Price comparisons"
                icon={Scale}
                color="orange"
              />
            </>
          )}
        </div>
      </div>

      {/* AI Insights Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-500" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">AI Market Highlights</h2>
              <p className="text-sm text-gray-500">
                {aiInsights?.count || 0} highlights • {aiInsights?.tier || 'free'} tier • refreshes {aiInsights?.refresh || 'daily'}
              </p>
            </div>
          </div>
          <a
            href="/opportunities"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
          >
            View all <ArrowRight className="w-4 h-4" />
          </a>
        </div>

        {insightsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <InsightCardSkeleton />
            <InsightCardSkeleton />
            <InsightCardSkeleton />
          </div>
        ) : insightsError ? (
          <div className="card text-center py-8">
            <p className="text-gray-500">Sign in to see AI highlights</p>
            <a href="/login" className="btn-primary mt-4 inline-block">Sign In</a>
          </div>
        ) : aiInsights?.insights?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {aiInsights.insights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No highlights yet</h3>
            <p className="text-gray-500 mt-1">
              AI highlights will appear here once market analysis runs
            </p>
          </div>
        )}

        {aiInsights?.upgrade_prompt && (
          <div className="mt-4 p-3 bg-primary-50 rounded-lg text-sm text-primary-700">
            {aiInsights.upgrade_prompt}
          </div>
        )}
      </div>

      {/* Cross-Platform Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-orange-500" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Cross-Platform Watch</h2>
              <p className="text-sm text-gray-500">
                Same markets, different prices on Kalshi vs Polymarket
              </p>
            </div>
          </div>
          <a
            href="/cross-platform"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
          >
            View all <ArrowRight className="w-4 h-4" />
          </a>
        </div>

        {crossLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <InsightCardSkeleton />
            <InsightCardSkeleton />
          </div>
        ) : crossPlatform?.matches?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {crossPlatform.matches.map((match) => (
              <CrossPlatformCard key={match.match_id} match={match} />
            ))}
          </div>
        ) : (
          <div className="card text-center py-8">
            <Scale className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No cross-platform matches</h3>
            <p className="text-gray-500 mt-1">
              Price comparisons will appear once matching markets are found
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
          <h3 className="font-semibold">Upgrade for More</h3>
          <p className="text-primary-100 text-sm mt-1">
            Get more highlights, movement analysis, and real-time updates
          </p>
          <a href="/settings" className="mt-4 inline-block bg-white text-primary-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-50 transition-colors">
            View Plans
          </a>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900">Browse Markets</h3>
          <p className="text-gray-500 text-sm mt-1">
            Explore all tracked prediction markets
          </p>
          <a
            href="/markets"
            className="mt-4 inline-block text-primary-600 text-sm font-medium hover:text-primary-700"
          >
            Browse →
          </a>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900">Set Up Alerts</h3>
          <p className="text-gray-500 text-sm mt-1">
            Get notified when markets move
          </p>
          <a
            href="/alerts"
            className="mt-4 inline-block text-primary-600 text-sm font-medium hover:text-primary-700"
          >
            Configure →
          </a>
        </div>
      </div>
    </div>
  )
}
