export interface Market {
  id: string
  platform: 'kalshi' | 'polymarket'
  title: string
  description?: string
  category?: string
  yes_price?: number
  no_price?: number
  volume?: number
  liquidity?: number
  status: string
  close_time?: string
  created_at: string
  updated_at: string
}

export interface Pattern {
  id: number
  market_id: string
  pattern_type: string
  description?: string
  confidence_score?: number
  profit_potential?: number
  time_sensitivity?: number
  risk_level?: number
  overall_score?: number
  status: string
  detected_at?: string
  expires_at?: string
  data?: Record<string, any>
}

export interface Opportunity extends Pattern {
  urgency: string
  risk_label: string
}

export interface Alert {
  id: number
  title: string
  message?: string
  action_suggestion?: string
  min_tier: string
  score: number
  pattern_type: string
  market_id: string
  time_sensitivity: number
  created_at: string
}

export interface MarketStats {
  kalshi_markets: number
  polymarket_markets: number
  total_markets: number
  total_volume: number
  last_collection?: string
}

export interface PatternStats {
  patterns_24h: Record<string, number>
  active_patterns: number
  avg_confidence_24h: number
  timestamp: string
}

export type PatternType =
  | 'volume_spike'
  | 'unusual_flow'
  | 'volume_divergence'
  | 'rapid_price_change'
  | 'trend_reversal'
  | 'support_break'
  | 'resistance_break'
  | 'cross_platform_arbitrage'
  | 'related_market_arbitrage'

export const PATTERN_LABELS: Record<PatternType, string> = {
  volume_spike: 'Volume Spike',
  unusual_flow: 'Unusual Flow',
  volume_divergence: 'Volume Divergence',
  rapid_price_change: 'Price Movement',
  trend_reversal: 'Trend Reversal',
  support_break: 'Support Break',
  resistance_break: 'Resistance Break',
  cross_platform_arbitrage: 'Cross-Platform Arb',
  related_market_arbitrage: 'Related Market Arb',
}

export const PATTERN_COLORS: Record<PatternType, string> = {
  volume_spike: 'bg-purple-100 text-purple-800',
  unusual_flow: 'bg-indigo-100 text-indigo-800',
  volume_divergence: 'bg-blue-100 text-blue-800',
  rapid_price_change: 'bg-orange-100 text-orange-800',
  trend_reversal: 'bg-pink-100 text-pink-800',
  support_break: 'bg-red-100 text-red-800',
  resistance_break: 'bg-green-100 text-green-800',
  cross_platform_arbitrage: 'bg-emerald-100 text-emerald-800',
  related_market_arbitrage: 'bg-teal-100 text-teal-800',
}
