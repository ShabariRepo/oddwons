'use client'

import { useState } from 'react'
import { Filter, RefreshCw } from 'lucide-react'
import { OpportunityCard, OpportunityCardSkeleton } from '@/components/OpportunityCard'
import { useOpportunities } from '@/hooks/useAPI'
import { triggerAnalysis } from '@/lib/api'
import { clsx } from 'clsx'

const tiers = [
  { id: 'basic', name: 'Basic', minScore: 70 },
  { id: 'premium', name: 'Premium', minScore: 50 },
  { id: 'pro', name: 'Pro', minScore: 30 },
]

export default function OpportunitiesPage() {
  const [selectedTier, setSelectedTier] = useState('basic')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { data, isLoading, mutate } = useOpportunities(selectedTier, 20)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await triggerAnalysis()
      await mutate()
    } catch (error) {
      console.error('Failed to refresh:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Opportunities</h1>
          <p className="text-gray-500 mt-1">
            AI-detected trading opportunities based on market patterns
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className={clsx('w-4 h-4', isRefreshing && 'animate-spin')} />
          {isRefreshing ? 'Analyzing...' : 'Refresh Analysis'}
        </button>
      </div>

      {/* Tier Filter */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filter by Tier</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {tiers.map((tier) => (
            <button
              key={tier.id}
              onClick={() => setSelectedTier(tier.id)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedTier === tier.id
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {tier.name}
              <span className="ml-1 text-xs opacity-75">(≥{tier.minScore})</span>
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-3">
          Showing opportunities with score ≥ {tiers.find(t => t.id === selectedTier)?.minScore}
        </p>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {data?.total_available || 0} opportunities found
        </p>
      </div>

      {/* Opportunities Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <OpportunityCardSkeleton key={i} />
          ))}
        </div>
      ) : data?.opportunities?.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data.opportunities.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onViewDetails={() => {
                console.log('View details:', opp)
              }}
            />
          ))}
        </div>
      ) : (
        <div className="card text-center py-16">
          <h3 className="text-lg font-medium text-gray-900">No opportunities found</h3>
          <p className="text-gray-500 mt-2 max-w-md mx-auto">
            No patterns match your current tier filter. Try selecting a different tier
            or wait for new opportunities to be detected.
          </p>
          <button
            onClick={handleRefresh}
            className="btn-primary mt-4"
          >
            Run Analysis
          </button>
        </div>
      )}
    </div>
  )
}
