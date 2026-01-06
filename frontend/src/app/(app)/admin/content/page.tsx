'use client'

import { useState } from 'react'
import { useAdminStats } from '@/hooks/useAPI'
import { getToken } from '@/lib/auth'
import { Brain, RefreshCw, Trash2, Database, Sparkles, AlertTriangle } from 'lucide-react'

export default function AdminContentPage() {
  const { data: stats, mutate: refreshStats } = useAdminStats()
  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleRegenerateInsights = async () => {
    if (!confirm('This will regenerate all AI insights. This may take several minutes. Continue?')) return

    setLoading('regenerate')
    setMessage(null)
    try {
      const token = getToken()
      const res = await fetch('/api/v1/admin/insights/regenerate', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to regenerate')
      setMessage({ type: 'success', text: 'Insights regeneration started. Check back in a few minutes.' })
      refreshStats()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(null)
    }
  }

  const handleClearStale = async () => {
    if (!confirm('Delete all expired/stale AI insights?')) return

    setLoading('clear')
    setMessage(null)
    try {
      const token = getToken()
      const res = await fetch('/api/v1/admin/insights/clear-stale', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to clear')
      setMessage({ type: 'success', text: data.message })
      refreshStats()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(null)
    }
  }

  const handleTriggerCollection = async () => {
    if (!confirm('Trigger data collection from Kalshi and Polymarket?')) return

    setLoading('collect')
    setMessage(null)
    try {
      const token = getToken()
      const res = await fetch('/api/v1/collect', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to collect')
      setMessage({ type: 'success', text: 'Data collection completed' })
      refreshStats()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Content Management</h2>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {message.type === 'error' && <AlertTriangle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Markets</p>
              <p className="text-2xl font-bold">{stats?.content?.total_markets?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active AI Insights</p>
              <p className="text-2xl font-bold">{stats?.content?.active_insights?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Sparkles className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Categories</p>
              <p className="text-2xl font-bold">8</p>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Data Collection */}
        <div className="card">
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Data Collection
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Manually trigger data collection from Kalshi and Polymarket APIs.
            This normally runs every 15 minutes automatically.
          </p>
          <button
            onClick={handleTriggerCollection}
            disabled={loading === 'collect'}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading === 'collect' ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Trigger Collection
          </button>
        </div>

        {/* AI Insights */}
        <div className="card">
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            AI Insights
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Regenerate AI insights using Gemini web search + Groq analysis.
            This will analyze all markets and create fresh highlights.
          </p>
          <button
            onClick={handleRegenerateInsights}
            disabled={loading === 'regenerate'}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading === 'regenerate' ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            Regenerate Insights
          </button>
        </div>

        {/* Clear Stale */}
        <div className="card">
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <Trash2 className="w-5 h-5" />
            Clear Stale Data
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Delete expired AI insights that are no longer relevant.
            This helps keep the database clean.
          </p>
          <button
            onClick={handleClearStale}
            disabled={loading === 'clear'}
            className="btn-danger w-full flex items-center justify-center gap-2"
          >
            {loading === 'clear' ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
            Clear Stale Insights
          </button>
        </div>

        {/* Info Card */}
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="font-semibold mb-2 text-blue-800">Pipeline Info</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Data collection runs every 15 minutes</li>
            <li>• AI analysis uses Gemini for web search</li>
            <li>• Groq generates insights with "bro vibes" tone</li>
            <li>• Insights are cached and refreshed periodically</li>
            <li>• Cross-platform matching uses fuzzy search</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
