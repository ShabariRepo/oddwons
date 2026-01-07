'use client'

import { useParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Newspaper, Calendar, Scale, Brain, Clock } from 'lucide-react'
import Link from 'next/link'
import { useInsightDetail } from '@/hooks/useAPI'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function InsightDetailPage() {
  const { id } = useParams()
  const { data, isLoading, error } = useInsightDetail(id as string)

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
          <div className="h-48 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="lg:ml-64 p-6">
        <Link href="/opportunities" className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Highlights
        </Link>
        <div className="card text-center py-12">
          <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Error loading insight</h3>
          <p className="text-gray-500 mt-2">Please sign in to view this insight</p>
          <Link href="/login" className="btn-primary mt-4 inline-block">Sign In</Link>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="lg:ml-64 p-6">
        <Link href="/opportunities" className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Highlights
        </Link>
        <div className="card text-center py-12">
          <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Insight not found</h3>
        </div>
      </div>
    )
  }

  const { insight, source_articles, market, price_history, cross_platform } = data

  const movementColor = insight.recent_movement?.includes('+')
    ? 'text-green-600'
    : insight.recent_movement?.includes('-')
    ? 'text-red-600'
    : 'text-gray-500'

  return (
    <div className="lg:ml-64 space-y-6 p-6">
      {/* Back Button */}
      <Link href="/opportunities" className="flex items-center gap-2 text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" />
        Back to Highlights
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            insight.platform === 'kalshi'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-purple-100 text-purple-800'
          }`}>
            {insight.platform}
          </span>
          {insight.category && (
            <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
              {insight.category}
            </span>
          )}
          {insight.recent_movement && (
            <span className={`flex items-center gap-1 text-sm font-medium ${movementColor}`}>
              {insight.recent_movement.includes('+') ? (
                <TrendingUp className="w-3 h-3" />
              ) : insight.recent_movement.includes('-') ? (
                <TrendingDown className="w-3 h-3" />
              ) : null}
              {insight.recent_movement}
            </span>
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{insight.market_title}</h1>
        <p className="text-gray-600">{insight.summary}</p>
      </div>

      {/* Current Odds */}
      {insight.current_odds && (
        <div className="grid grid-cols-2 gap-4">
          <div className="card bg-green-50">
            <p className="text-sm text-green-600 font-medium">Yes</p>
            <p className="text-3xl font-bold text-green-700">
              {(insight.current_odds.yes * 100).toFixed(0)}%
            </p>
          </div>
          <div className="card bg-red-50">
            <p className="text-sm text-red-600 font-medium">No</p>
            <p className="text-3xl font-bold text-red-700">
              {(insight.current_odds.no * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* Implied Probability */}
      {insight.implied_probability && (
        <div className="card bg-primary-50">
          <p className="text-primary-700 font-medium">{insight.implied_probability}</p>
        </div>
      )}

      {/* Price History Chart */}
      {price_history && price_history.length > 1 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Price History</h2>
          <div className="h-48">
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
                  formatter={(v) => [`${(Number(v) * 100).toFixed(1)}%`, 'Yes']}
                  labelFormatter={(t) => t ? new Date(t as number).toLocaleString() : ''}
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

      {/* AI Analysis - The Good Stuff */}
      {insight.analyst_note && (
        <div className="card border-l-4 border-primary-500">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary-500" />
            AI Analysis
          </h2>
          <p className="text-gray-700 whitespace-pre-wrap">{insight.analyst_note}</p>
        </div>
      )}

      {/* Movement Context */}
      {insight.movement_context && (
        <div className="card bg-blue-50">
          <p className="text-sm font-medium text-blue-800 flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4" />
            Why It Moved
          </p>
          <p className="text-blue-700">{insight.movement_context}</p>
        </div>
      )}

      {/* Upcoming Catalyst */}
      {insight.upcoming_catalyst && (
        <div className="card bg-yellow-50">
          <p className="text-sm font-medium text-yellow-800 flex items-center gap-2 mb-2">
            <Calendar className="w-4 h-4" />
            Upcoming Catalyst
          </p>
          <p className="text-yellow-700">{insight.upcoming_catalyst}</p>
        </div>
      )}

      {/* Source Articles - THE HOMEWORK */}
      {source_articles && source_articles.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Newspaper className="w-5 h-5" />
            Source Articles
            <span className="text-xs text-gray-500 font-normal">(our homework)</span>
          </h2>
          <div className="space-y-3">
            {source_articles.map((article: any, i: number) => (
              <div
                key={i}
                className="p-3 bg-gray-50 rounded-lg"
              >
                <p className="font-medium text-gray-900">{article.title}</p>
                <p className="text-sm text-gray-500">
                  {article.source}{article.date ? ` - ${article.date}` : ''}
                </p>
                {article.relevance && (
                  <p className="text-xs text-gray-400 mt-1">{article.relevance}</p>
                )}
              </div>
            ))}
          </div>
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
          {cross_platform.gap_cents && (
            <p className="text-sm text-gray-500 mt-3">
              {cross_platform.gap_cents.toFixed(1)}% gap between platforms
            </p>
          )}
        </div>
      )}

      {/* Volume Note */}
      {insight.volume_note && (
        <div className="card">
          <p className="text-sm text-gray-500">Volume: {insight.volume_note}</p>
        </div>
      )}

      {/* Trade Links */}
      {market && (
        <div className="card bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Trade This Market</h2>
          <div className="flex flex-wrap gap-3">
            <a
              href={market.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary flex items-center gap-2"
            >
              Open on {market.platform}
              <ExternalLink className="w-4 h-4" />
            </a>
            <Link
              href={`/markets/${market.id}`}
              className="btn-secondary flex items-center gap-2"
            >
              View Market Details
            </Link>
          </div>
          {market.close_time && (
            <p className="text-sm text-gray-500 mt-3 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Closes: {new Date(market.close_time).toLocaleDateString()}
            </p>
          )}
        </div>
      )}

      {/* Tier Info */}
      <div className="text-xs text-gray-400 text-center">
        Viewing as {data.tier} tier
        {data.tier !== 'pro' && (
          <span> - <Link href="/settings" className="text-primary-600 hover:underline">Upgrade</Link> for more insights</span>
        )}
      </div>
    </div>
  )
}
