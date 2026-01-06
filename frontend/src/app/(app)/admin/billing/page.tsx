'use client'

import { useState, useEffect } from 'react'
import { getToken } from '@/lib/auth'
import { CreditCard, RefreshCw, ExternalLink, AlertTriangle, CheckCircle } from 'lucide-react'

interface WebhookEvent {
  id: string
  type: string
  created: string
  data: {
    object_id: string | null
  }
}

export default function AdminBillingPage() {
  const [events, setEvents] = useState<WebhookEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = getToken()
      const res = await fetch('/api/v1/admin/webhook-logs?limit=100', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch webhook logs')
      const data = await res.json()
      setEvents(data.events || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents()
  }, [])

  const getEventIcon = (type: string) => {
    if (type.includes('succeeded') || type.includes('created') || type.includes('paid')) {
      return <CheckCircle className="w-4 h-4 text-green-500" />
    }
    if (type.includes('failed') || type.includes('deleted') || type.includes('canceled')) {
      return <AlertTriangle className="w-4 h-4 text-red-500" />
    }
    return <CreditCard className="w-4 h-4 text-blue-500" />
  }

  const getEventColor = (type: string) => {
    if (type.includes('succeeded') || type.includes('created') || type.includes('paid')) {
      return 'bg-green-50 text-green-800'
    }
    if (type.includes('failed') || type.includes('deleted') || type.includes('canceled')) {
      return 'bg-red-50 text-red-800'
    }
    return 'bg-blue-50 text-blue-800'
  }

  // Group events by type for stats
  const eventStats = events.reduce((acc, e) => {
    const category = e.type.split('.')[0]
    acc[category] = (acc[category] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Billing & Webhooks</h2>
        <div className="flex items-center gap-4">
          <a
            href="https://dashboard.stripe.com"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary flex items-center gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            Stripe Dashboard
          </a>
          <button
            onClick={fetchEvents}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      {/* Event Type Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {Object.entries(eventStats).map(([category, count]) => (
          <div key={category} className="card text-center">
            <p className="text-2xl font-bold">{count}</p>
            <p className="text-sm text-gray-500 capitalize">{category}</p>
          </div>
        ))}
      </div>

      {/* Webhook Events Table */}
      <div className="card overflow-hidden p-0">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h3 className="font-semibold">Recent Webhook Events</h3>
          <p className="text-sm text-gray-500">Last 100 events from Stripe</p>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No webhook events found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Event ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Object ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {events.map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {getEventIcon(event.type)}
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getEventColor(event.type)}`}>
                          {event.type}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={`https://dashboard.stripe.com/events/${event.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-mono text-blue-600 hover:underline"
                      >
                        {event.id.slice(0, 20)}...
                      </a>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-600">
                      {event.data.object_id ? event.data.object_id.slice(0, 20) + '...' : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(event.created).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Links */}
      <div className="card">
        <h3 className="font-semibold mb-4">Quick Links</h3>
        <div className="flex flex-wrap gap-3">
          <a
            href="https://dashboard.stripe.com/subscriptions"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm flex items-center gap-2"
          >
            <CreditCard className="w-4 h-4" />
            Subscriptions
          </a>
          <a
            href="https://dashboard.stripe.com/customers"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm flex items-center gap-2"
          >
            <CreditCard className="w-4 h-4" />
            Customers
          </a>
          <a
            href="https://dashboard.stripe.com/invoices"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm flex items-center gap-2"
          >
            <CreditCard className="w-4 h-4" />
            Invoices
          </a>
          <a
            href="https://dashboard.stripe.com/webhooks"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm flex items-center gap-2"
          >
            <CreditCard className="w-4 h-4" />
            Webhooks
          </a>
        </div>
      </div>
    </div>
  )
}
