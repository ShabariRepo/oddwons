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
  cross_platform_arbitrage: 'Cross-Platform Gap',
  related_market_arbitrage: 'Related Market Gap',
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

// AI Insights types
export interface AIInsight {
  id: number
  market_id: string
  market_title: string
  platform: string
  category: string
  summary: string
  current_odds?: { yes: number; no: number }
  implied_probability?: string
  volume_note?: string
  recent_movement?: string
  movement_context?: string
  upcoming_catalyst?: string
  analyst_note?: string
  created_at: string
}

export interface AIInsightsResponse {
  insights: AIInsight[]
  count: number
  tier: string
  refresh: string
  upgrade_prompt?: string
}

// Cross-Platform types
export interface CrossPlatformMatch {
  match_id: string
  topic: string
  category?: string
  kalshi_market_id?: string
  kalshi_title?: string
  kalshi_yes_price?: number
  kalshi_volume?: number
  polymarket_market_id?: string
  polymarket_title?: string
  polymarket_yes_price?: number
  polymarket_volume?: number
  price_gap_cents: number
  gap_direction: string
  combined_volume: number
  similarity_score?: number
}

export interface CrossPlatformSpotlight extends CrossPlatformMatch {
  ai_analysis?: string
  gap_explanation?: string
  momentum_summary?: string
  key_risks?: string
  news_headlines?: { title: string; source?: string; date?: string }[]
  kalshi_url?: string
  polymarket_url?: string
  last_updated: string
}

// Daily Digest types
export interface DailyDigest {
  headline?: string
  generated_at?: string
  top_movers?: Array<{ market_id: string; title: string; change: number }>
  most_active?: Array<{ market_id: string; title: string; volume: number }>
  category_snapshots?: Record<string, string>
  upcoming_catalysts?: Array<{ date: string; description: string }>
  cross_platform_watch?: {
    matches: Array<{
      topic: string
      kalshi_price: number
      polymarket_price: number
      gap_cents: number
      combined_volume: number
      summary: string
    }>
    total_matches: number
    total_volume: number
  }
}

export interface InsightStats {
  active_highlights: number
  categories_covered: number
  price_gap_findings: number
  highlights_by_category: Record<string, number>
  last_updated: string
}
