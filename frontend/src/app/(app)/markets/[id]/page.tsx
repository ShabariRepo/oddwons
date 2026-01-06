'use client'

import { useParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Brain, Scale, Clock, BarChart3, Newspaper } from 'lucide-react'
import Link from 'next/link'
import { useMarketDetail } from '@/hooks/useAPI'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function MarketDetailPage() {
  const { id } = useParams()
  const { data, isLoading, error } = useMarketDetail(id as string)

  if (isLoading) {
    return (
      <div className="lg:ml-64 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded-lg"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-24 bg-gray-200 rounded-lg"></div>
            <div className="h-24 bg-gray-200 rounded-lg"></div>
          </div>
          <div className="h-64 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="lg:ml-64 p-6">
        <Link href="/markets" className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Markets
        </Link>
        <div className="card text-center py-12">
          <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Error loading market</h3>
          <p className="text-gray-500 mt-2">Please try again later</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="lg:ml-64 p-6">
        <Link href="/markets" className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Markets
        </Link>
        <div className="card text-center py-12">
          <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Market not found</h3>
        </div>
      </div>
    )
  }

  const { market, price_history, ai_insight, cross_platform } = data

  const formatVolume = (vol?: number) => {
    if (!vol) return '-'
    if (vol >= 1000000) return `$${(vol / 1000000).toFixed(1)}M`
    if (vol >= 1000) return `$${(vol / 1000).toFixed(0)}K`
    return `$${vol.toFixed(0)}`
  }

  return (
    <div className="lg:ml-64 space-y-6 p-6">
      {/* Back Button */}
      <Link href="/markets" className="flex items-center gap-2 text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" />
        Back to Markets
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            market.platform === 'kalshi'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-purple-100 text-purple-800'
          }`}>
            {market.platform}
          </span>
          {market.category && (
            <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
              {market.category}
            </span>
          )}
          <span className={`px-2 py-1 rounded text-xs ${
            market.status === 'active'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-600'
          }`}>
            {market.status}
          </span>
          {market.has_ai_highlight && (
            <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800 flex items-center gap-1">
              <Brain className="w-3 h-3" /> AI Insight
            </span>
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{market.title}</h1>

        {market.close_time && (
          <p className="text-sm text-gray-500 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            Closes: {new Date(market.close_time).toLocaleDateString()}
          </p>
        )}
      </div>

      {/* Current Odds */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card bg-green-50">
          <p className="text-sm text-green-600 font-medium">Yes</p>
          <p className="text-3xl font-bold text-green-700">
            {market.yes_price ? `${(market.yes_price * 100).toFixed(0)}%` : '-'}
          </p>
          {market.price_change_24h && (
            <p className={`text-sm mt-1 flex items-center gap-1 ${
              market.price_change_24h > 0 ? 'text-green-600' : market.price_change_24h < 0 ? 'text-red-600' : 'text-gray-500'
            }`}>
              {market.price_change_24h > 0 ? <TrendingUp className="w-3 h-3" /> : market.price_change_24h < 0 ? <TrendingDown className="w-3 h-3" /> : null}
              {market.price_change_24h > 0 ? '+' : ''}{market.price_change_24h.toFixed(1)}% (24h)
            </p>
          )}
        </div>
        <div className="card bg-red-50">
          <p className="text-sm text-red-600 font-medium">No</p>
          <p className="text-3xl font-bold text-red-700">
            {market.no_price ? `${(market.no_price * 100).toFixed(0)}%` : '-'}
          </p>
        </div>
      </div>

      {/* Volume Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Volume</p>
          <p className="text-xl font-bold text-gray-900">
            {formatVolume(market.volume)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">24h Volume</p>
          <p className="text-xl font-bold text-gray-900">
            {formatVolume(market.volume_24h)}
          </p>
        </div>
      </div>

      {/* Additional Stats */}
      {(market.price_change_7d !== undefined || market.volume_rank !== undefined) && (
        <div className="grid grid-cols-2 gap-4">
          {market.price_change_7d !== undefined && (
            <div className="card">
              <p className="text-sm text-gray-500">7-Day Change</p>
              <p className={`text-xl font-bold ${
                market.price_change_7d > 0 ? 'text-green-600' : market.price_change_7d < 0 ? 'text-red-600' : 'text-gray-900'
              }`}>
                {market.price_change_7d > 0 ? '+' : ''}{market.price_change_7d.toFixed(1)}%
              </p>
            </div>
          )}
          {market.volume_rank !== undefined && market.volume_rank !== null && (
            <div className="card">
              <p className="text-sm text-gray-500">Volume Rank (Category)</p>
              <p className="text-xl font-bold text-gray-900">
                Top {100 - market.volume_rank}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* Price History Chart */}
      {price_history && price_history.length > 1 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Price History</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={price_history}>
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(t) => t ? new Date(t).toLocaleDateString() : ''}
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                />
                <Tooltip
                  formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, 'Yes']}
                  labelFormatter={(t) => t ? new Date(t).toLocaleString() : ''}
                />
                <Line
                  type="monotone"
                  dataKey="yes_price"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* AI Insight - if exists */}
      {ai_insight && (
        <div className="card border-l-4 border-purple-500">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-500" />
            AI Analysis
          </h2>
          {ai_insight.summary && (
            <p className="text-gray-600 mb-3">{ai_insight.summary}</p>
          )}
          {ai_insight.analyst_note && (
            <p className="text-gray-700 whitespace-pre-wrap mb-4">{ai_insight.analyst_note}</p>
          )}

          {ai_insight.upcoming_catalyst && (
            <div className="p-3 bg-yellow-50 rounded-lg mb-4">
              <p className="text-sm font-medium text-yellow-800">Upcoming Catalyst</p>
              <p className="text-yellow-700 mt-1">{ai_insight.upcoming_catalyst}</p>
            </div>
          )}

          {ai_insight.movement_context && (
            <div className="p-3 bg-blue-50 rounded-lg mb-4">
              <p className="text-sm font-medium text-blue-800">Why It Moved</p>
              <p className="text-blue-700 mt-1">{ai_insight.movement_context}</p>
            </div>
          )}

          {/* Source Articles */}
          {ai_insight.source_articles && ai_insight.source_articles.length > 0 && (
            <div className="border-t pt-4">
              <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Newspaper className="w-4 h-4" />
                Sources (our homework)
              </p>
              <div className="space-y-2">
                {ai_insight.source_articles.map((article: any, i: number) => (
                  <div key={i} className="text-sm text-gray-600">
                    {article.title} <span className="text-gray-400">({article.source})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Link
            href={`/insights/${ai_insight.id}`}
            className="text-sm text-purple-600 hover:underline mt-3 inline-block"
          >
            View full insight
          </Link>
        </div>
      )}

      {/* Cross-Platform Comparison */}
      {cross_platform && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Scale className="w-5 h-5" />
            Cross-Platform Pricing
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600 font-medium">Kalshi</p>
              <p className="text-2xl font-bold text-blue-800">
                {cross_platform.kalshi_price ? `${(cross_platform.kalshi_price * 100).toFixed(0)}%` : 'N/A'}
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-600 font-medium">Polymarket</p>
              <p className="text-2xl font-bold text-purple-800">
                {cross_platform.polymarket_price ? `${(cross_platform.polymarket_price * 100).toFixed(0)}%` : 'N/A'}
              </p>
            </div>
          </div>
          {cross_platform.price_gap && (
            <p className="text-sm text-gray-500 mt-3">
              {(cross_platform.price_gap * 100).toFixed(1)}% gap between platforms
            </p>
          )}
          <p className="text-sm text-gray-400 mt-2">
            Topic: {cross_platform.topic}
          </p>
        </div>
      )}

      {/* Trade Links */}
      <div className="card bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Trade This Market</h2>
        <a
          href={market.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary inline-flex items-center gap-2"
        >
          Open on {market.platform}
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  )
}
