'use client'

import { useState } from 'react'
import { useAdminUsers } from '@/hooks/useAPI'
import { Search, RefreshCw, ChevronRight } from 'lucide-react'
import Link from 'next/link'
import { getToken } from '@/lib/auth'

export default function AdminUsersPage() {
  const [search, setSearch] = useState('')
  const [tierFilter, setTierFilter] = useState('')
  const { data, isLoading, mutate } = useAdminUsers({ search, tier: tierFilter })

  const handleSync = async (userId: string) => {
    const token = getToken()
    const res = await fetch(`/api/v1/admin/users/${userId}/sync-subscription`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    const result = await res.json()
    alert(result.message)
    mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Users</h2>
        <span className="text-gray-500">{data?.total || 0} total</span>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by email or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>
        <select
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="">All Tiers</option>
          <option value="free">Free</option>
          <option value="basic">Basic</option>
          <option value="premium">Premium</option>
          <option value="pro">Pro</option>
        </select>
      </div>

      {/* Users Table */}
      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Tier</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Joined</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data?.users?.map((user: any) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium">{user.email}</p>
                      <p className="text-xs text-gray-500">{user.name || 'No name'}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      user.subscription_tier === 'PRO' ? 'bg-amber-100 text-amber-800' :
                      user.subscription_tier === 'PREMIUM' ? 'bg-purple-100 text-purple-800' :
                      user.subscription_tier === 'BASIC' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {user.subscription_tier?.toLowerCase() || 'free'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-600">
                      {user.subscription_status || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleSync(user.id)}
                        className="p-1 hover:bg-gray-100 rounded"
                        title="Sync Subscription"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                      <Link
                        href={`/admin/users/${user.id}`}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
