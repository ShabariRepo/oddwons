'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAdminUser } from '@/hooks/useAPI'
import { syncUserSubscription, changeUserTier, grantUserTrial } from '@/lib/api'
import { getToken } from '@/lib/auth'
import { ArrowLeft, RefreshCw, CreditCard, Clock, Shield, ExternalLink, AlertTriangle, Trash2, Zap } from 'lucide-react'

interface StripeSubscription {
  id: string
  status: string
  price_id: string
  current_period_end: string
  trial_end: string | null
  cancel_at_period_end: boolean
  created: string
}

interface StripeSubscriptionsData {
  customer_id: string
  subscriptions: StripeSubscription[]
  count: number
  has_duplicates: boolean
}

export default function AdminUserDetailPage() {
  const params = useParams()
  const router = useRouter()
  const userId = params.id as string
  const { data, isLoading, mutate } = useAdminUser(userId)

  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [stripeData, setStripeData] = useState<StripeSubscriptionsData | null>(null)
  const [loadingStripe, setLoadingStripe] = useState(false)

  // Fetch Stripe subscriptions
  const fetchStripeSubscriptions = async () => {
    setLoadingStripe(true)
    try {
      const token = getToken()
      const res = await fetch(`/api/v1/admin/users/${userId}/stripe-subscriptions`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setStripeData(data)
      }
    } catch (err) {
      console.error('Failed to fetch Stripe subscriptions:', err)
    } finally {
      setLoadingStripe(false)
    }
  }

  useEffect(() => {
    if (userId) {
      fetchStripeSubscriptions()
    }
  }, [userId])

  const handleSync = async () => {
    setLoading('sync')
    setMessage(null)
    try {
      const result = await syncUserSubscription(userId)
      setMessage({ type: 'success', text: result.message })
      mutate()
      fetchStripeSubscriptions()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Sync failed' })
    } finally {
      setLoading(null)
    }
  }

  const handleChangeTier = async (tier: string) => {
    if (!confirm(`Change tier to ${tier.toUpperCase()}?`)) return
    setLoading('tier')
    setMessage(null)
    try {
      const result = await changeUserTier(userId, tier)
      setMessage({ type: 'success', text: result.message })
      mutate()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to change tier' })
    } finally {
      setLoading(null)
    }
  }

  const handleGrantTrial = async (days: number) => {
    if (!confirm(`Grant ${days} day trial?`)) return
    setLoading('trial')
    setMessage(null)
    try {
      const result = await grantUserTrial(userId, days)
      setMessage({ type: 'success', text: result.message })
      mutate()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to grant trial' })
    } finally {
      setLoading(null)
    }
  }

  const handleCancelSubscription = async (subId: string, immediately: boolean) => {
    const action = immediately ? 'cancel immediately' : 'cancel at period end'
    if (!confirm(`Are you sure you want to ${action} subscription ${subId.slice(0, 15)}...?`)) return

    setLoading(`cancel-${subId}`)
    setMessage(null)
    try {
      const token = getToken()
      const res = await fetch(
        `/api/v1/admin/users/${userId}/cancel-stripe-subscription/${subId}?immediately=${immediately}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      )
      const result = await res.json()
      if (!res.ok) throw new Error(result.detail || 'Failed to cancel')
      setMessage({ type: 'success', text: result.message })
      mutate()
      fetchStripeSubscriptions()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(null)
    }
  }

  const handleCleanupDuplicates = async () => {
    if (!confirm('This will cancel all duplicate subscriptions, keeping only the newest. Continue?')) return

    setLoading('cleanup')
    setMessage(null)
    try {
      const token = getToken()
      const res = await fetch(`/api/v1/admin/users/${userId}/cleanup-duplicate-subscriptions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const result = await res.json()
      if (!res.ok) throw new Error(result.detail || 'Failed to cleanup')
      setMessage({ type: 'success', text: result.message })
      mutate()
      fetchStripeSubscriptions()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(null)
    }
  }

  if (isLoading) return <div className="text-gray-500">Loading...</div>
  if (!data?.user) return <div className="text-red-500">User not found</div>

  const { user, stripe_subscription } = data
  const activeSubs = stripeData?.subscriptions.filter(s => s.status === 'active' || s.status === 'trialing') || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-xl font-semibold">{user.email}</h2>
          <p className="text-gray-500">{user.name || 'No name'}</p>
        </div>
        {user.is_admin && (
          <span className="px-2 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded">
            Admin
          </span>
        )}
      </div>

      {/* Duplicate Warning */}
      {stripeData?.has_duplicates && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-600" />
            <div>
              <p className="font-medium text-yellow-800">This user has duplicate subscriptions!</p>
              <p className="text-sm text-yellow-700">{activeSubs.length} active/trialing subscriptions found</p>
            </div>
          </div>
          <button
            onClick={handleCleanupDuplicates}
            disabled={loading === 'cleanup'}
            className="btn-primary bg-yellow-600 hover:bg-yellow-700 flex items-center gap-2"
          >
            {loading === 'cleanup' ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            Cleanup Duplicates
          </button>
        </div>
      )}

      {/* Messages */}
      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Info Card */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            User Info
          </h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-gray-500">ID</dt>
              <dd className="font-mono text-sm">{user.id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Email</dt>
              <dd>{user.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Name</dt>
              <dd>{user.name || '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Joined</dt>
              <dd>{user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Last Login</dt>
              <dd>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</dd>
            </div>
          </dl>
        </div>

        {/* Subscription Card */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            DB Subscription
          </h3>
          <dl className="space-y-3">
            <div className="flex justify-between items-center">
              <dt className="text-gray-500">Tier</dt>
              <dd>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  user.subscription_tier === 'PRO' ? 'bg-amber-100 text-amber-800' :
                  user.subscription_tier === 'PREMIUM' ? 'bg-purple-100 text-purple-800' :
                  user.subscription_tier === 'BASIC' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {user.subscription_tier || 'FREE'}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Status</dt>
              <dd className={`font-medium ${
                user.subscription_status === 'ACTIVE' ? 'text-green-600' :
                user.subscription_status === 'TRIALING' ? 'text-blue-600' :
                user.subscription_status === 'PAST_DUE' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {user.subscription_status || 'INACTIVE'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Trial End</dt>
              <dd>{user.trial_end ? new Date(user.trial_end).toLocaleDateString() : '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Subscription End</dt>
              <dd>{user.subscription_end ? new Date(user.subscription_end).toLocaleDateString() : '-'}</dd>
            </div>
          </dl>

          <div className="mt-4 pt-4 border-t">
            <button
              onClick={handleSync}
              disabled={loading === 'sync'}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              {loading === 'sync' ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Sync from Stripe
            </button>
          </div>
        </div>

        {/* Stripe Subscriptions Card - Full Width */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <CreditCard className="w-5 h-5" />
              All Stripe Subscriptions
              {stripeData && (
                <span className="text-sm font-normal text-gray-500">({stripeData.count} total)</span>
              )}
            </h3>
            <button
              onClick={fetchStripeSubscriptions}
              disabled={loadingStripe}
              className="btn-secondary text-sm flex items-center gap-1"
            >
              {loadingStripe ? (
                <RefreshCw className="w-3 h-3 animate-spin" />
              ) : (
                <RefreshCw className="w-3 h-3" />
              )}
              Refresh
            </button>
          </div>

          {!stripeData?.subscriptions.length ? (
            <p className="text-gray-500">No Stripe subscriptions found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">ID</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Status</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Created</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Period End</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {stripeData.subscriptions.map((sub) => (
                    <tr key={sub.id} className={`${
                      sub.status === 'active' || sub.status === 'trialing' ? 'bg-green-50' : ''
                    }`}>
                      <td className="px-3 py-2">
                        <a
                          href={`https://dashboard.stripe.com/subscriptions/${sub.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-blue-600 hover:underline flex items-center gap-1"
                        >
                          {sub.id.slice(0, 18)}...
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          sub.status === 'active' ? 'bg-green-100 text-green-800' :
                          sub.status === 'trialing' ? 'bg-blue-100 text-blue-800' :
                          sub.status === 'canceled' ? 'bg-gray-100 text-gray-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {sub.status}
                          {sub.cancel_at_period_end && ' (canceling)'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {new Date(sub.created).toLocaleDateString()}
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {new Date(sub.current_period_end).toLocaleDateString()}
                      </td>
                      <td className="px-3 py-2">
                        {(sub.status === 'active' || sub.status === 'trialing') && !sub.cancel_at_period_end && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleCancelSubscription(sub.id, false)}
                              disabled={loading === `cancel-${sub.id}`}
                              className="text-orange-600 hover:text-orange-800 text-xs"
                              title="Cancel at period end"
                            >
                              {loading === `cancel-${sub.id}` ? '...' : 'End of Period'}
                            </button>
                            <button
                              onClick={() => handleCancelSubscription(sub.id, true)}
                              disabled={loading === `cancel-${sub.id}`}
                              className="text-red-600 hover:text-red-800 text-xs flex items-center gap-1"
                              title="Cancel immediately"
                            >
                              <Trash2 className="w-3 h-3" />
                              Now
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {user.stripe_customer_id && (
            <div className="mt-4 pt-4 border-t">
              <a
                href={`https://dashboard.stripe.com/customers/${user.stripe_customer_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                View Customer in Stripe Dashboard
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>

        {/* Actions Card */}
        <div className="card lg:col-span-2">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Admin Actions
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Change Tier */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Change Tier (DB Only)</label>
              <div className="flex gap-2 flex-wrap">
                {['free', 'basic', 'premium', 'pro'].map((tier) => (
                  <button
                    key={tier}
                    onClick={() => handleChangeTier(tier)}
                    disabled={loading === 'tier' || user.subscription_tier?.toLowerCase() === tier}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      user.subscription_tier?.toLowerCase() === tier
                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                    }`}
                  >
                    {tier.toUpperCase()}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">This only changes the database, not Stripe</p>
            </div>

            {/* Grant Trial */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Grant Trial (DB Only)</label>
              <div className="flex gap-2">
                {[7, 14, 30].map((days) => (
                  <button
                    key={days}
                    onClick={() => handleGrantTrial(days)}
                    disabled={loading === 'trial'}
                    className="px-3 py-1.5 rounded text-sm font-medium bg-blue-100 hover:bg-blue-200 text-blue-700 transition-colors"
                  >
                    {days} days
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">Sets trial_end and status in DB</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
