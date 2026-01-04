'use client'

import { BarChart3, TrendingUp, Activity, PieChart } from 'lucide-react'
import { usePatternStats, useMarketStats } from '@/hooks/useAPI'
import { PATTERN_LABELS, PatternType } from '@/lib/types'

export default function AnalyticsPage() {
  const { data: patternStats, isLoading: pLoading } = usePatternStats()
  const { data: marketStats, isLoading: mLoading } = useMarketStats()

  const isLoading = pLoading || mLoading

  const patternCounts = patternStats?.patterns_24h || {}

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-500 mt-1">
          Performance metrics and pattern statistics
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Markets Tracked</p>
              <p className="text-xl font-bold text-gray-900">
                {isLoading ? '-' : marketStats?.total_markets}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Activity className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active Patterns</p>
              <p className="text-xl font-bold text-gray-900">
                {isLoading ? '-' : patternStats?.active_patterns}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Confidence</p>
              <p className="text-xl font-bold text-gray-900">
                {isLoading ? '-' : `${patternStats?.avg_confidence_24h}%`}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <PieChart className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Patterns (24h)</p>
              <p className="text-xl font-bold text-gray-900">
                {isLoading ? '-' : Object.values(patternCounts).reduce((a: number, b: any) => a + (b as number), 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Markets by Platform</h2>
          {isLoading ? (
            <div className="h-48 animate-pulse bg-gray-100 rounded"></div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Kalshi</span>
                  <span className="font-medium">{marketStats?.kalshi_markets}</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{
                      width: `${(marketStats?.kalshi_markets || 0) / (marketStats?.total_markets || 1) * 100}%`
                    }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Polymarket</span>
                  <span className="font-medium">{marketStats?.polymarket_markets}</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full"
                    style={{
                      width: `${(marketStats?.polymarket_markets || 0) / (marketStats?.total_markets || 1) * 100}%`
                    }}
                  ></div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Patterns by Type (24h)</h2>
          {isLoading ? (
            <div className="h-48 animate-pulse bg-gray-100 rounded"></div>
          ) : (
            <div className="space-y-3">
              {Object.entries(patternCounts).length > 0 ? (
                Object.entries(patternCounts).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {PATTERN_LABELS[type as PatternType] || type}
                    </span>
                    <span className="text-sm font-medium text-gray-900">{count as number}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">
                  No patterns detected in the last 24 hours
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Coming Soon */}
      <div className="card bg-gradient-to-br from-gray-50 to-gray-100 text-center py-12">
        <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900">More Analytics Coming Soon</h3>
        <p className="text-gray-500 mt-2 max-w-md mx-auto">
          Historical performance tracking, success rate analysis, and custom reports
          will be available in a future update.
        </p>
      </div>
    </div>
  )
}
