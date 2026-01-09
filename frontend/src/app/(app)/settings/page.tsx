'use client'

import { useState } from 'react'
import { User, Bell, CreditCard, Shield, Check, Loader2, ExternalLink } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '@/components/AuthProvider'
import { createCheckout, createPortal, changePassword } from '@/lib/auth'
import SparkleCard from '@/components/SparkleCard'

const plans = [
  {
    id: 'basic',
    name: 'Basic',
    price: 9.99,
    features: [
      'Daily market digest',
      'Top 10 market highlights',
      'Email notifications',
      'Price movement alerts',
      '7-day free trial',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 19.99,
    features: [
      'Everything in Basic',
      'Full movement analysis',
      'Upcoming catalysts',
      'Cross-platform price comparisons',
      'SMS notifications',
      'Historical price data',
      '7-day free trial',
    ],
    recommended: true,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 29.99,
    features: [
      'Everything in Premium',
      'Full analyst notes',
      'Real-time updates',
      'API access',
      'Priority support',
      'Early access to new features',
      '7-day free trial',
    ],
  },
]

export default function SettingsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('subscription')
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Security form state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const currentTier = user?.subscription_tier
  const hasSubscription = currentTier && user?.subscription_status === 'active'

  const handleUpgrade = async (planId: string) => {

    setLoading(planId)
    setError('')

    try {
      const { checkout_url } = await createCheckout(planId)
      window.location.href = checkout_url
    } catch (err: any) {
      setError(err.message || 'Failed to create checkout session')
    } finally {
      setLoading(null)
    }
  }

  const handleManageSubscription = async () => {
    setLoading('portal')
    setError('')

    try {
      const { portal_url } = await createPortal()
      window.location.href = portal_url
    } catch (err: any) {
      setError(err.message || 'Failed to open billing portal')
    } finally {
      setLoading(null)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match')
      return
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading('password')
    setError('')
    setSuccess('')

    try {
      await changePassword(currentPassword, newPassword)
      setSuccess('Password changed successfully')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err: any) {
      setError(err.message || 'Failed to change password')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">
          Manage your account and subscription
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-8">
          {[
            { id: 'subscription', name: 'Subscription', icon: CreditCard },
            { id: 'notifications', name: 'Notifications', icon: Bell },
            { id: 'account', name: 'Account', icon: User },
            { id: 'security', name: 'Security', icon: Shield },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 pb-4 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'subscription' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Plan</h2>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={clsx(
                  'p-3 rounded-lg',
                  hasSubscription ? 'bg-primary-100' : 'bg-gray-100'
                )}>
                  <CreditCard className={clsx(
                    'w-6 h-6',
                    hasSubscription ? 'text-primary-600' : 'text-gray-400'
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {hasSubscription
                      ? `${currentTier!.charAt(0).toUpperCase() + currentTier!.slice(1)} Plan`
                      : 'No Active Plan'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {user?.subscription_status === 'trialing'
                      ? 'Free trial active'
                      : user?.subscription_status === 'active'
                        ? 'Active subscription'
                        : 'Start a 7-day free trial below'}
                  </p>
                </div>
              </div>
              {hasSubscription && (
                <button
                  onClick={handleManageSubscription}
                  disabled={loading === 'portal'}
                  className="btn-secondary flex items-center gap-2"
                >
                  {loading === 'portal' && <Loader2 className="w-4 h-4 animate-spin" />}
                  <ExternalLink className="w-4 h-4" />
                  Manage Billing
                </button>
              )}
            </div>
          </div>

          <h2 className="text-lg font-semibold text-gray-900">Available Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const isTrialing = user?.subscription_status === 'trialing'
              const isActive = user?.subscription_status === 'active'
              const isCurrent = (isActive || isTrialing) && plan.id === currentTier
              const hasAnySubscription = isActive || isTrialing

              // Calculate if this is an upgrade or downgrade
              const currentIndex = hasAnySubscription ? plans.findIndex(p => p.id === currentTier) : -1
              const planIndex = plans.findIndex(p => p.id === plan.id)
              const isUpgrade = !hasAnySubscription || planIndex > currentIndex
              const isDowngrade = hasAnySubscription && planIndex < currentIndex

              // Determine button text
              const getButtonText = () => {
                if (isCurrent) return 'Current Plan'
                if (!hasAnySubscription) return 'Start Free Trial'
                if (isTrialing) return `Switch to ${plan.name}`
                if (isUpgrade) return `Upgrade to ${plan.name}`
                return `Downgrade to ${plan.name}`
              }

              return (
                <SparkleCard
                  key={plan.id}
                  active={isCurrent}
                  className="rounded-2xl"
                >
                  <div
                    className={clsx(
                      'card relative',
                      isCurrent
                        ? 'border-2 border-yellow-400 shadow-[0_0_30px_rgba(251,191,36,0.3)] bg-gradient-to-b from-yellow-50 to-white'
                        : plan.recommended
                          ? 'ring-2 ring-primary-500'
                          : ''
                    )}
                  >
                    {isCurrent && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                        <span className="bg-gradient-to-r from-yellow-400 to-amber-500 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg flex items-center gap-1">
                          <span>👤</span> YOU
                        </span>
                      </div>
                    )}
                    {plan.recommended && !isCurrent && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <span className="bg-primary-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                          Recommended
                        </span>
                      </div>
                    )}

                    <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                    <p className="mt-2">
                      <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                      <span className="text-gray-500">/month</span>
                    </p>

                    {/* Show trial status if on trial for this plan */}
                    {isTrialing && isCurrent && (
                      <p className="mt-1 text-xs text-amber-600 font-medium">
                        Trial active
                      </p>
                    )}

                    <ul className="mt-6 space-y-3">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-2">
                          <Check className="w-5 h-5 text-green-500 shrink-0" />
                          <span className="text-sm text-gray-600">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <button
                      onClick={() => isCurrent ? undefined : isDowngrade ? handleManageSubscription() : handleUpgrade(plan.id)}
                      className={clsx(
                        'w-full mt-6 flex justify-center items-center gap-2',
                        isCurrent
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed py-2.5 rounded-lg font-medium'
                          : isUpgrade
                            ? 'btn-primary'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300 py-2.5 rounded-lg font-medium'
                      )}
                      disabled={isCurrent || loading === plan.id}
                    >
                      {loading === plan.id && <Loader2 className="w-4 h-4 animate-spin" />}
                      {getButtonText()}
                    </button>
                  </div>
                </SparkleCard>
              )
            })}
          </div>
        </div>
      )}

      {activeTab === 'notifications' && (
        <div className="card space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Notification Preferences</h2>

          {[
            { id: 'email', label: 'Email Notifications', desc: 'Receive daily digest and alerts via email' },
            { id: 'push', label: 'Push Notifications', desc: 'Browser notifications for high-priority alerts' },
            { id: 'price_gap', label: 'Price Gap Alerts', desc: 'Notify me about cross-platform price differences' },
            { id: 'volume', label: 'Volume Spike Alerts', desc: 'Notify me about unusual volume activity' },
            { id: 'price', label: 'Price Movement Alerts', desc: 'Notify me about rapid price changes' },
          ].map((item) => (
            <div key={item.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
              <div>
                <p className="font-medium text-gray-900">{item.label}</p>
                <p className="text-sm text-gray-500">{item.desc}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>
          ))}

          <button className="btn-primary">Save Preferences</button>
        </div>
      )}

      {activeTab === 'account' && (
        <div className="card space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Account Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                defaultValue={user?.name || ''}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <button className="btn-primary">Update Account</button>
        </div>
      )}

      {activeTab === 'security' && (
        <form onSubmit={handleChangePassword} className="card space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Change Password</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading === 'password'}
            className="btn-primary flex items-center gap-2"
          >
            {loading === 'password' && <Loader2 className="w-4 h-4 animate-spin" />}
            Change Password
          </button>
        </form>
      )}
    </div>
  )
}
