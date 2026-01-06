'use client'

import { useState, useEffect } from 'react'
import { useAdminHealth } from '@/hooks/useAPI'
import { Activity, Database, Server, CreditCard, RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

export default function AdminSystemPage() {
  const { data: health, isLoading, mutate } = useAdminHealth()
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  useEffect(() => {
    if (health) {
      setLastChecked(new Date())
    }
  }, [health])

  const getStatusIcon = (status: string) => {
    if (status === 'healthy') {
      return <CheckCircle className="w-6 h-6 text-green-500" />
    }
    if (status.startsWith('error')) {
      return <XCircle className="w-6 h-6 text-red-500" />
    }
    return <AlertTriangle className="w-6 h-6 text-yellow-500" />
  }

  const getStatusColor = (status: string) => {
    if (status === 'healthy') return 'bg-green-50 border-green-200'
    if (status.startsWith('error')) return 'bg-red-50 border-red-200'
    return 'bg-yellow-50 border-yellow-200'
  }

  const getStatusText = (status: string) => {
    if (status === 'healthy') return 'text-green-800'
    if (status.startsWith('error')) return 'text-red-800'
    return 'text-yellow-800'
  }

  const services = [
    {
      name: 'Database',
      key: 'database',
      icon: Database,
      description: 'PostgreSQL connection',
    },
    {
      name: 'Redis',
      key: 'redis',
      icon: Server,
      description: 'Cache and sessions',
    },
    {
      name: 'Stripe',
      key: 'stripe',
      icon: CreditCard,
      description: 'Payment processing',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">System Health</h2>
          {lastChecked && (
            <p className="text-sm text-gray-500">
              Last checked: {lastChecked.toLocaleTimeString()}
            </p>
          )}
        </div>
        <button
          onClick={() => mutate()}
          disabled={isLoading}
          className="btn-primary flex items-center gap-2"
        >
          {isLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Refresh
        </button>
      </div>

      {/* Overall Status */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className={`p-4 rounded-full ${
            health && Object.values(health).every(s => s === 'healthy')
              ? 'bg-green-100'
              : 'bg-red-100'
          }`}>
            <Activity className={`w-8 h-8 ${
              health && Object.values(health).every(s => s === 'healthy')
                ? 'text-green-600'
                : 'text-red-600'
            }`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold">
              {isLoading
                ? 'Checking...'
                : health && Object.values(health).every(s => s === 'healthy')
                ? 'All Systems Operational'
                : 'Some Services Degraded'}
            </h3>
            <p className="text-gray-500">
              {services.filter(s => health?.[s.key as keyof typeof health] === 'healthy').length} of {services.length} services healthy
            </p>
          </div>
        </div>
      </div>

      {/* Service Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {services.map((service) => {
          const status = health?.[service.key as keyof typeof health] || 'unknown'
          return (
            <div
              key={service.key}
              className={`card border-2 ${getStatusColor(status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white rounded-lg shadow-sm">
                    <service.icon className="w-6 h-6 text-gray-700" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{service.name}</h3>
                    <p className="text-sm text-gray-500">{service.description}</p>
                  </div>
                </div>
                {getStatusIcon(status)}
              </div>
              <div className={`mt-4 pt-4 border-t ${getStatusText(status)}`}>
                <p className="text-sm font-medium capitalize">
                  {status === 'healthy' ? 'Healthy' : status}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Environment Info */}
      <div className="card">
        <h3 className="font-semibold mb-4">Environment</h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-500">API Version</dt>
            <dd className="font-mono">v0.1.0</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Environment</dt>
            <dd className="font-mono">{process.env.NODE_ENV || 'development'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Data Collection</dt>
            <dd className="font-mono">Every 15 minutes</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">AI Provider</dt>
            <dd className="font-mono">Gemini + Groq</dd>
          </div>
        </dl>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="font-semibold mb-4">Quick Diagnostics</h3>
        <div className="space-y-2 text-sm">
          <p className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            Health endpoint: <code className="bg-gray-100 px-2 py-0.5 rounded">/health</code>
          </p>
          <p className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            API docs: <code className="bg-gray-100 px-2 py-0.5 rounded">/docs</code>
          </p>
          <p className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            Admin health: <code className="bg-gray-100 px-2 py-0.5 rounded">/api/v1/admin/health</code>
          </p>
        </div>
      </div>
    </div>
  )
}
