'use client'

import { useState } from 'react'
import { User, Bell, CreditCard, Shield, Check } from 'lucide-react'
import { clsx } from 'clsx'

const plans = [
  {
    id: 'basic',
    name: 'Basic',
    price: 9.99,
    features: [
      'Daily market analysis digest',
      'Top 5 opportunities',
      'Email notifications',
      'Basic pattern alerts',
    ],
    current: true,
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 19.99,
    features: [
      'Everything in Basic',
      'Real-time opportunity alerts',
      'Custom alert parameters',
      'SMS notifications',
      'Discord/Slack integration',
      'Historical performance data',
    ],
    recommended: true,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 29.99,
    features: [
      'Everything in Premium',
      'Custom analysis parameters',
      'Advanced pattern detection',
      'API access',
      'Priority support',
      'Early access to new features',
    ],
  },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('subscription')

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">
          Manage your account and subscription
        </p>
      </div>

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
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary-100 rounded-lg">
                <CreditCard className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Basic Plan</p>
                <p className="text-sm text-gray-500">$9.99/month • Renews on Feb 1, 2026</p>
              </div>
            </div>
          </div>

          <h2 className="text-lg font-semibold text-gray-900">Available Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={clsx(
                  'card relative',
                  plan.recommended && 'ring-2 ring-primary-500'
                )}
              >
                {plan.recommended && (
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

                <ul className="mt-6 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <Check className="w-5 h-5 text-green-500 shrink-0" />
                      <span className="text-sm text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={clsx(
                    'w-full mt-6',
                    plan.current
                      ? 'btn-secondary'
                      : 'btn-primary'
                  )}
                  disabled={plan.current}
                >
                  {plan.current ? 'Current Plan' : 'Upgrade'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'notifications' && (
        <div className="card space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Notification Preferences</h2>

          {[
            { id: 'email', label: 'Email Notifications', desc: 'Receive daily digest and alerts via email' },
            { id: 'push', label: 'Push Notifications', desc: 'Browser notifications for high-priority alerts' },
            { id: 'arbitrage', label: 'Arbitrage Alerts', desc: 'Notify me about cross-platform opportunities' },
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
                defaultValue="user@example.com"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                defaultValue="User"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <button className="btn-primary">Update Account</button>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="card space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Security Settings</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <button className="btn-primary">Change Password</button>
        </div>
      )}
    </div>
  )
}
