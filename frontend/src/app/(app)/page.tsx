'use client'

import { TrendingUp, Zap, BarChart3, Clock } from 'lucide-react'
import { StatsCard, StatsCardSkeleton } from '@/components/StatsCard'
import { OpportunityCard, OpportunityCardSkeleton } from '@/components/OpportunityCard'
import { useMarketStats, useOpportunities, usePatternStats } from '@/hooks/useAPI'

export default function Dashboard() {
  const { data: marketStats, isLoading: statsLoading } = useMarketStats()
  const { data: patternStats } = usePatternStats()
  const { data: opportunities, isLoading: oppsLoading } = useOpportunities('basic', 6)

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
        <p className="text-gray-500 mt-1">Real-time prediction market analysis</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              title="Total Markets"
              value={marketStats?.total_markets || 0}
              subtitle={`${marketStats?.kalshi_markets || 0} Kalshi, ${marketStats?.polymarket_markets || 0} Poly`}
              icon={TrendingUp}
              color="blue"
            />
            <StatsCard
              title="Active Patterns"
              value={patternStats?.active_patterns || 0}
              subtitle="Detected opportunities"
              icon={Zap}
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
              title="Last Update"
              value={formatTime(marketStats?.last_collection)}
              subtitle="Data collection"
              icon={Clock}
              color="orange"
            />
          </>
        )}
      </div>

      {/* Opportunities Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Top Opportunities</h2>
            <p className="text-sm text-gray-500">
              {opportunities?.total_available || 0} opportunities available for your tier
            </p>
          </div>
          <a
            href="/opportunities"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all
          </a>
        </div>

        {oppsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <OpportunityCardSkeleton />
            <OpportunityCardSkeleton />
            <OpportunityCardSkeleton />
          </div>
        ) : opportunities?.opportunities?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {opportunities.opportunities.map((opp) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                onViewDetails={() => {
                  // TODO: Open detail modal
                  console.log('View details:', opp)
                }}
              />
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <Zap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No opportunities yet</h3>
            <p className="text-gray-500 mt-1">
              Opportunities will appear here once the system detects patterns
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
          <h3 className="font-semibold">Upgrade to Premium</h3>
          <p className="text-primary-100 text-sm mt-1">
            Get real-time alerts and access to more patterns
          </p>
          <button className="mt-4 bg-white text-primary-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-50 transition-colors">
            Upgrade Now
          </button>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900">Pattern Types</h3>
          <p className="text-gray-500 text-sm mt-1">
            Learn about different pattern types we detect
          </p>
          <a
            href="/patterns/types"
            className="mt-4 inline-block text-primary-600 text-sm font-medium hover:text-primary-700"
          >
            Learn more →
          </a>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900">Configure Alerts</h3>
          <p className="text-gray-500 text-sm mt-1">
            Customize which patterns trigger notifications
          </p>
          <a
            href="/settings"
            className="mt-4 inline-block text-primary-600 text-sm font-medium hover:text-primary-700"
          >
            Settings →
          </a>
        </div>
      </div>
    </div>
  )
}
