'use client'

import { clsx } from 'clsx'
import { Clock, TrendingUp, AlertTriangle, Zap, ArrowRight } from 'lucide-react'
import { Opportunity, PATTERN_LABELS, PATTERN_COLORS, PatternType } from '@/lib/types'

interface OpportunityCardProps {
  opportunity: Opportunity
  onViewDetails?: () => void
}

export function OpportunityCard({ opportunity, onViewDetails }: OpportunityCardProps) {
  const score = opportunity.overall_score || 0
  const patternType = opportunity.pattern_type as PatternType

  // Traffic light color based on score
  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-500'
    if (score >= 50) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getScoreBg = (score: number) => {
    if (score >= 70) return 'bg-green-50 border-green-200'
    if (score >= 50) return 'bg-yellow-50 border-yellow-200'
    return 'bg-red-50 border-red-200'
  }

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'Act Now':
        return <Zap className="w-4 h-4 text-red-500" />
      case 'High Priority':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  return (
    <div className={clsx('card border-2 transition-all hover:shadow-md', getScoreBg(score))}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <span className={clsx('score-badge text-xs', PATTERN_COLORS[patternType] || 'bg-gray-100 text-gray-800')}>
            {PATTERN_LABELS[patternType] || patternType}
          </span>
          <div className="flex items-center gap-2 mt-2">
            {getUrgencyIcon(opportunity.urgency)}
            <span className="text-sm font-medium text-gray-700">{opportunity.urgency}</span>
          </div>
        </div>

        {/* Score Circle */}
        <div className={clsx('flex flex-col items-center')}>
          <div className={clsx(
            'w-14 h-14 rounded-full flex items-center justify-center border-4',
            score >= 70 ? 'border-green-400 bg-green-50' :
            score >= 50 ? 'border-yellow-400 bg-yellow-50' :
            'border-red-400 bg-red-50'
          )}>
            <span className={clsx('text-lg font-bold', getScoreColor(score))}>
              {Math.round(score)}
            </span>
          </div>
          <span className="text-xs text-gray-500 mt-1">Score</span>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
        {opportunity.description}
      </p>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Confidence</p>
          <p className="text-lg font-semibold text-gray-900">
            {opportunity.confidence_score?.toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Profit</p>
          <p className="text-lg font-semibold text-gray-900">
            {opportunity.profit_potential?.toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Risk</p>
          <p className="text-lg font-semibold text-gray-900">
            {opportunity.risk_label}
          </p>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={onViewDetails}
        className="w-full btn-primary flex items-center justify-center gap-2"
      >
        View Details
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  )
}

export function OpportunityCardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="h-5 w-24 bg-gray-200 rounded"></div>
          <div className="h-4 w-20 bg-gray-200 rounded mt-2"></div>
        </div>
        <div className="w-14 h-14 bg-gray-200 rounded-full"></div>
      </div>
      <div className="h-10 bg-gray-200 rounded mb-4"></div>
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-12 bg-gray-200 rounded"></div>
        <div className="h-12 bg-gray-200 rounded"></div>
      </div>
      <div className="h-10 bg-gray-200 rounded"></div>
    </div>
  )
}
