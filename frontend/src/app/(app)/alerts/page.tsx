'use client'

import { useState } from 'react'
import { Bell, Clock, TrendingUp, Zap, AlertTriangle } from 'lucide-react'
import { useAlerts } from '@/hooks/useAPI'
import { clsx } from 'clsx'
import { Alert, PATTERN_LABELS, PatternType } from '@/lib/types'

function AlertCard({ alert }: { alert: Alert }) {
  const getIcon = () => {
    switch (alert.time_sensitivity) {
      case 5:
        return <Zap className="w-5 h-5 text-red-500" />
      case 4:
        return <AlertTriangle className="w-5 h-5 text-orange-500" />
      default:
        return <Bell className="w-5 h-5 text-blue-500" />
    }
  }

  const formatTime = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)

    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className="p-2 rounded-lg bg-gray-100">
          {getIcon()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-medium text-gray-900">{alert.title}</h3>
              <span className={clsx(
                'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-1',
                'bg-gray-100 text-gray-700'
              )}>
                {PATTERN_LABELS[alert.pattern_type as PatternType] || alert.pattern_type}
              </span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              {formatTime(alert.created_at)}
            </div>
          </div>

          {alert.message && (
            <p className="text-sm text-gray-600 mt-2 whitespace-pre-line">
              {alert.message}
            </p>
          )}

          {alert.action_suggestion && (
            <div className="mt-3 p-3 bg-primary-50 rounded-lg">
              <p className="text-sm text-primary-800">
                <strong>Suggested Action:</strong> {alert.action_suggestion}
              </p>
            </div>
          )}

          <div className="flex items-center gap-4 mt-3">
            <span className="text-sm text-gray-500">
              Score: <span className="font-medium text-gray-900">{alert.score}</span>
            </span>
            <span className={clsx(
              'text-xs px-2 py-0.5 rounded',
              alert.min_tier === 'basic' ? 'bg-gray-100 text-gray-700' :
              alert.min_tier === 'premium' ? 'bg-purple-100 text-purple-700' :
              'bg-yellow-100 text-yellow-700'
            )}>
              {alert.min_tier} tier
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function AlertSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-start gap-4">
        <div className="w-9 h-9 bg-gray-200 rounded-lg"></div>
        <div className="flex-1">
          <div className="h-5 w-1/2 bg-gray-200 rounded"></div>
          <div className="h-4 w-20 bg-gray-200 rounded mt-2"></div>
          <div className="h-16 bg-gray-200 rounded mt-3"></div>
        </div>
      </div>
    </div>
  )
}

export default function AlertsPage() {
  const [tier, setTier] = useState('basic')
  const { data, isLoading } = useAlerts(tier, 20)

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-500 mt-1">
            Notifications for detected patterns and opportunities
          </p>
        </div>

        {/* Tier Filter */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Show alerts for:</span>
          <select
            value={tier}
            onChange={(e) => setTier(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="basic">Basic</option>
            <option value="premium">Premium</option>
            <option value="pro">Pro</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Bell className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Alerts</p>
              <p className="text-xl font-bold text-gray-900">{data?.count || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Zap className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">High Priority</p>
              <p className="text-xl font-bold text-gray-900">
                {data?.alerts?.filter(a => a.time_sensitivity >= 4).length || 0}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Score</p>
              <p className="text-xl font-bold text-gray-900">
                {data?.alerts?.length
                  ? Math.round(data.alerts.reduce((acc, a) => acc + a.score, 0) / data.alerts.length)
                  : 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {isLoading ? (
          [...Array(5)].map((_, i) => <AlertSkeleton key={i} />)
        ) : data?.alerts?.length ? (
          data.alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))
        ) : (
          <div className="card text-center py-16">
            <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No alerts yet</h3>
            <p className="text-gray-500 mt-2 max-w-md mx-auto">
              Alerts will appear here when the system detects patterns matching your preferences
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
