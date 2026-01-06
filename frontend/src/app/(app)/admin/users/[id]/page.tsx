'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAdminUser } from '@/hooks/useAPI'
import { syncUserSubscription, changeUserTier, grantUserTrial } from '@/lib/api'
import { ArrowLeft, RefreshCw, CreditCard, Clock, Shield, ExternalLink } from 'lucide-react'
import Link from 'next/link'

export default function AdminUserDetailPage() {
  const params = useParams()
  const router = useRouter()
  const userId = params.id as string
  const { data, isLoading, mutate } = useAdminUser(userId)

  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleSync = async () => {
    setLoading('sync')
    setMessage(null)
    try {
      const result = await syncUserSubscription(userId)
      setMessage({ type: 'success', text: result.message })
      mutate()
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

  if (isLoading) return <div className="text-gray-500">Loading...</div>
  if (!data?.user) return <div className="text-red-500">User not found</div>

  const { user, stripe_subscription } = data

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
            Subscription
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

        {/* Stripe Info Card */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Stripe Details
          </h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-gray-500">Customer ID</dt>
              <dd className="font-mono text-sm">
                {user.stripe_customer_id ? (
                  <a
                    href={`https://dashboard.stripe.com/customers/${user.stripe_customer_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1"
                  >
                    {user.stripe_customer_id.slice(0, 20)}...
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : '-'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Subscription ID</dt>
              <dd className="font-mono text-sm">
                {user.stripe_subscription_id ? (
                  <a
                    href={`https://dashboard.stripe.com/subscriptions/${user.stripe_subscription_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1"
                  >
                    {user.stripe_subscription_id.slice(0, 20)}...
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : '-'}
              </dd>
            </div>
          </dl>

          {stripe_subscription && (
            <div className="mt-4 pt-4 border-t">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Live Stripe Status</h4>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Status</dt>
                  <dd className={`font-medium ${
                    stripe_subscription.status === 'active' ? 'text-green-600' :
                    stripe_subscription.status === 'trialing' ? 'text-blue-600' :
                    'text-red-600'
                  }`}>
                    {stripe_subscription.status}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Period End</dt>
                  <dd>{new Date(stripe_subscription.current_period_end * 1000).toLocaleDateString()}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Cancel at Period End</dt>
                  <dd>{stripe_subscription.cancel_at_period_end ? 'Yes' : 'No'}</dd>
                </div>
              </dl>
            </div>
          )}
        </div>

        {/* Actions Card */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Admin Actions
          </h3>

          <div className="space-y-4">
            {/* Change Tier */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Change Tier</label>
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
            </div>

            {/* Grant Trial */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Grant Trial</label>
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
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
