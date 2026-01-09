'use client'

import { useState } from 'react'
import { Search, Filter, ExternalLink, Brain } from 'lucide-react'
import { useMarkets } from '@/hooks/useAPI'
import { clsx } from 'clsx'
import { Market } from '@/lib/types'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { PLATFORMS } from '@/lib/platforms'

const platforms = [
  { id: '', name: 'All Platforms' },
  { id: 'kalshi', name: 'Kalshi' },
  { id: 'polymarket', name: 'Polymarket' },
]

function MarketRow({ market }: { market: Market }) {
  const router = useRouter()
  const yesPrice = market.yes_price ? (market.yes_price * 100).toFixed(1) : '-'
  const noPrice = market.no_price ? (market.no_price * 100).toFixed(1) : '-'

  // Platform colors
  const platformColor = market.platform === 'kalshi' ? '#00D26A' : '#6366F1'
  const platformLogo = market.platform === 'kalshi'
    ? '/logos/kalshi-logo.png'
    : '/logos/polymarket-logo.png'

  const formatVolume = (vol?: number) => {
    if (!vol) return '-'
    if (vol >= 1000000) return `$${(vol / 1000000).toFixed(1)}M`
    if (vol >= 1000) return `$${(vol / 1000).toFixed(0)}K`
    return `$${vol.toFixed(0)}`
  }

  const handleRowClick = () => {
    router.push(`/markets/${market.id}`)
  }

  const handleExternalClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    const url = market.platform === 'kalshi'
      ? `https://kalshi.com/markets/${market.id}`
      : `https://polymarket.com/event/${market.id}`
    window.open(url, '_blank')
  }

  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer relative overflow-hidden transition-all duration-200 hover:scale-[1.01] hover:shadow-md hover:z-10"
      onClick={handleRowClick}
    >
      <td className="px-4 py-4">
        <div className="flex items-start gap-3">
          {/* Platform logo + vertical color bar */}
          <div className="relative flex items-center gap-2 shrink-0">
            <div
              className="w-1 h-10 rounded-full"
              style={{ backgroundColor: platformColor }}
            />
            <Image
              src={platformLogo}
              alt={market.platform}
              width={20}
              height={20}
              className="rounded-sm"
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {market.title}
            </p>
            {market.category && (
              <p className="text-xs text-gray-500 mt-0.5">{market.category}</p>
            )}
          </div>
        </div>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-sm font-medium text-green-600">{yesPrice}¢</span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-sm font-medium text-red-600">{noPrice}¢</span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-sm text-gray-900">{formatVolume(market.volume)}</span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className={clsx(
          'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
          market.status === 'active'
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-800'
        )}>
          {market.status}
        </span>
      </td>
      <td className="px-4 py-4 text-right">
        {/* Diagonal gradient - 50% of entire row width, positioned relative to <tr> */}
        <div
          className="absolute right-0 top-0 bottom-0 w-1/2 pointer-events-none"
          style={{
            background: `linear-gradient(115deg, transparent 0%, transparent 30%, ${platformColor}15 30%, ${platformColor}35 100%)`,
          }}
        />
        <button
          className="text-gray-400 hover:text-gray-600 relative z-10"
          onClick={handleExternalClick}
          title="Open on platform"
        >
          <ExternalLink className="w-4 h-4" />
        </button>
      </td>
    </tr>
  )
}

function MarketRowSkeleton() {
  return (
    <tr>
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-6 h-5 bg-gray-200 rounded animate-pulse"></div>
          <div className="flex-1">
            <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-3 w-1/4 bg-gray-200 rounded animate-pulse mt-1"></div>
          </div>
        </div>
      </td>
      <td className="px-4 py-4"><div className="h-4 w-12 bg-gray-200 rounded animate-pulse mx-auto"></div></td>
      <td className="px-4 py-4"><div className="h-4 w-12 bg-gray-200 rounded animate-pulse mx-auto"></div></td>
      <td className="px-4 py-4"><div className="h-4 w-16 bg-gray-200 rounded animate-pulse mx-auto"></div></td>
      <td className="px-4 py-4"><div className="h-5 w-14 bg-gray-200 rounded-full animate-pulse mx-auto"></div></td>
      <td className="px-4 py-4"><div className="h-4 w-4 bg-gray-200 rounded animate-pulse ml-auto"></div></td>
    </tr>
  )
}

export default function MarketsPage() {
  const [platform, setPlatform] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useMarkets({
    platform: platform || undefined,
    page,
    page_size: 20,
  })

  const filteredMarkets = data?.markets?.filter(m =>
    !search || m.title.toLowerCase().includes(search.toLowerCase())
  ) || []

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Markets</h1>
        <p className="text-gray-500 mt-1">
          Browse all tracked prediction markets from Kalshi and Polymarket
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search markets..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Platform Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {platforms.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="text-sm text-gray-600">
        {data?.total || 0} markets found
      </div>

      {/* Markets Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Market
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Yes
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wide">
                  No
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Volume
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Link
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                [...Array(10)].map((_, i) => <MarketRowSkeleton key={i} />)
              ) : filteredMarkets.length ? (
                filteredMarkets.map((market) => (
                  <MarketRow key={market.id} market={market} />
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">
                    No markets found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              Page {page} of {Math.ceil(data.total / 20)}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(data.total / 20)}
                className="btn-secondary text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
