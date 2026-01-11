'use client'

import { useState, useEffect } from 'react'
import {
  Twitter,
  Power,
  PowerOff,
  Send,
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw
} from 'lucide-react'
import * as api from '@/lib/api'

interface XPost {
  id: string
  tweet_id: string | null
  tweet_url: string | null
  post_type: string
  status: string
  content: string
  has_image: boolean
  error_message: string | null
  created_at: string | null
  posted_at: string | null
}

interface XBotSettings {
  enabled: boolean
  morning_movers_enabled: boolean
  platform_comparison_enabled: boolean
  market_highlight_enabled: boolean
  weekly_recap_enabled: boolean
  promo_enabled: boolean
  max_posts_per_day: number
  updated_at: string | null
}

interface XPostStats {
  totals: { total: number; posted: number; failed: number }
  recent: { last_24h: number; last_7d: number }
  by_type: Record<string, number>
  bot_enabled: boolean
}

export default function XBotAdminPage() {
  const [settings, setSettings] = useState<XBotSettings | null>(null)
  const [stats, setStats] = useState<XPostStats | null>(null)
  const [posts, setPosts] = useState<XPost[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [selectedPost, setSelectedPost] = useState<XPost | null>(null)

  // Load data
  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [settingsRes, statsRes, postsRes] = await Promise.all([
        api.getXBotSettings(),
        api.getXPostStats(),
        api.getXPosts({ page_size: 20 }),
      ])
      setSettings(settingsRes.settings)
      setStats(statsRes)
      setPosts(postsRes.posts)
    } catch (err) {
      console.error('Failed to load X bot data:', err)
    }
    setLoading(false)
  }

  async function handleToggleBot() {
    if (!settings) return
    setActionLoading('toggle')
    try {
      const res = await api.toggleXBot(!settings.enabled)
      setSettings(res.settings)
    } catch (err) {
      console.error('Failed to toggle bot:', err)
    }
    setActionLoading(null)
  }

  async function handleTogglePostType(postType: string, currentEnabled: boolean) {
    setActionLoading(postType)
    try {
      const res = await api.toggleXPostType(postType, !currentEnabled)
      setSettings(res.settings)
    } catch (err) {
      console.error('Failed to toggle post type:', err)
    }
    setActionLoading(null)
  }

  async function handleTriggerPost(postType: string) {
    setActionLoading(`trigger-${postType}`)
    try {
      await api.triggerXPost(postType)
      // Reload posts after trigger
      const postsRes = await api.getXPosts({ page_size: 20 })
      setPosts(postsRes.posts)
    } catch (err) {
      console.error('Failed to trigger post:', err)
    }
    setActionLoading(null)
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'posted':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  function getPostTypeLabel(postType: string) {
    const labels: Record<string, string> = {
      morning_movers: 'Morning Movers',
      platform_comparison: 'Platform Gap',
      market_highlight: 'Market Highlight',
      weekly_recap: 'Weekly Recap',
      daily_stats: 'Daily Stats',
      promo: 'Daily Promo',
      manual: 'Manual',
    }
    return labels[postType] || postType
  }

  if (loading) {
    return <div className="text-gray-500">Loading X Bot data...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Twitter className="w-6 h-6" />
          X Bot Management
        </h2>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Master Toggle */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Bot Status</h3>
            <p className="text-sm text-gray-500">
              {settings?.enabled ? 'Bot is active and posting on schedule' : 'Bot is paused - no posts will be made'}
            </p>
          </div>
          <button
            onClick={handleToggleBot}
            disabled={actionLoading === 'toggle'}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
              settings?.enabled
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {settings?.enabled ? (
              <>
                <PowerOff className="w-5 h-5" />
                Pause Bot
              </>
            ) : (
              <>
                <Power className="w-5 h-5" />
                Enable Bot
              </>
            )}
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <p className="text-2xl font-bold">{stats.totals.total}</p>
            <p className="text-sm text-gray-500">Total Posts</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-green-600">{stats.totals.posted}</p>
            <p className="text-sm text-gray-500">Posted</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-red-600">{stats.totals.failed}</p>
            <p className="text-sm text-gray-500">Failed</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold">{stats.recent.last_24h}</p>
            <p className="text-sm text-gray-500">Last 24h</p>
          </div>
        </div>
      )}

      {/* Post Type Controls */}
      <div className="card">
        <h3 className="font-semibold mb-4">Post Types</h3>
        <div className="space-y-3">
          {[
            { key: 'morning_movers', label: 'Morning Movers', time: 'Every 2hrs (8AM, 4PM)', triggerKey: 'morning' },
            { key: 'platform_comparison', label: 'Platform Gap', time: 'Every 2hrs (10AM, 2PM, 8PM)', triggerKey: 'afternoon' },
            { key: 'market_highlight', label: 'Market Highlight', time: 'Every 2hrs (12PM, 6PM, 10PM)', triggerKey: 'evening' },
            { key: 'promo', label: 'Daily Promo', time: '7:00 PM EST (with logo)', triggerKey: 'promo' },
            { key: 'weekly_recap', label: 'Weekly Recap', time: 'Sun 10 AM EST', triggerKey: 'weekly' },
          ].map((pt) => {
            const settingKey = `${pt.key}_enabled` as keyof XBotSettings
            const isEnabled = settings?.[settingKey] as boolean

            return (
              <div key={pt.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium">{pt.label}</p>
                  <p className="text-xs text-gray-500">{pt.time}</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleTriggerPost(pt.triggerKey)}
                    disabled={actionLoading === `trigger-${pt.triggerKey}` || !settings?.enabled}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-sky-100 text-sky-700 hover:bg-sky-200 rounded disabled:opacity-50"
                  >
                    <Send className="w-4 h-4" />
                    Post Now
                  </button>
                  <button
                    onClick={() => handleTogglePostType(pt.key, isEnabled)}
                    disabled={actionLoading === pt.key}
                    className={`px-3 py-1.5 text-sm rounded font-medium ${
                      isEnabled
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {isEnabled ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Posts */}
      <div className="card">
        <h3 className="font-semibold mb-4">Recent Posts</h3>
        <div className="space-y-2">
          {posts.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No posts yet</p>
          ) : (
            posts.map((post) => (
              <div
                key={post.id}
                onClick={() => setSelectedPost(selectedPost?.id === post.id ? null : post)}
                className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(post.status)}
                    <div>
                      <p className="font-medium">{getPostTypeLabel(post.post_type)}</p>
                      <p className="text-xs text-gray-500">{formatDate(post.posted_at || post.created_at)}</p>
                    </div>
                  </div>
                  {post.tweet_url && (
                    <a
                      href={post.tweet_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1 text-sm text-sky-600 hover:text-sky-700"
                    >
                      View <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>

                {/* Expanded content */}
                {selectedPost?.id === post.id && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Content:</p>
                      <pre className="text-sm bg-white p-2 rounded whitespace-pre-wrap font-mono">
                        {post.content}
                      </pre>
                    </div>
                    {post.error_message && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Error:</p>
                        <p className="text-sm text-red-600 bg-red-50 p-2 rounded">
                          {post.error_message}
                        </p>
                      </div>
                    )}
                    {post.has_image && (
                      <p className="text-xs text-gray-500">Has attached image</p>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
