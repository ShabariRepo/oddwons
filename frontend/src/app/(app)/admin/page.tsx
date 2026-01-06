'use client'

import { useAdminStats } from '@/hooks/useAPI'
import { Users, DollarSign, TrendingUp, Brain } from 'lucide-react'

export default function AdminDashboard() {
  const { data: stats, isLoading } = useAdminStats()

  if (isLoading) return <div className="text-gray-500">Loading...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Dashboard</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Users</p>
              <p className="text-2xl font-bold">{stats?.users?.total || 0}</p>
            </div>
          </div>
          <p className="text-xs text-green-600 mt-2">+{stats?.users?.new_7d || 0} this week</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Est. MRR</p>
              <p className="text-2xl font-bold">${stats?.revenue?.estimated_mrr || 0}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">{stats?.revenue?.paid_users || 0} paid users</p>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Trialing</p>
              <p className="text-2xl font-bold">{stats?.users?.trialing || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Brain className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">AI Insights</p>
              <p className="text-2xl font-bold">{stats?.content?.active_insights || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tier Distribution */}
      <div className="card">
        <h3 className="font-semibold mb-4">Tier Distribution</h3>
        <div className="grid grid-cols-4 gap-4">
          {Object.entries(stats?.tiers || {}).map(([tier, count]) => (
            <div key={tier} className="text-center">
              <p className="text-2xl font-bold">{count as number}</p>
              <p className="text-sm text-gray-500 capitalize">{tier}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
