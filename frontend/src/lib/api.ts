import { getToken } from './auth'

const API_BASE = '/api/v1'

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options?.headers,
    },
  })

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }

  return res.json()
}

// Markets
export async function getMarkets(params?: {
  platform?: string
  category?: string
  status?: string
  page?: number
  page_size?: number
}) {
  const searchParams = new URLSearchParams()
  if (params?.platform) searchParams.set('platform', params.platform)
  if (params?.category) searchParams.set('category', params.category)
  if (params?.status) searchParams.set('status', params.status)
  if (params?.page) searchParams.set('page', params.page.toString())
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString())

  return fetchAPI<{
    markets: import('./types').Market[]
    total: number
    page: number
    page_size: number
  }>(`/markets?${searchParams}`)
}

export async function getMarket(id: string) {
  return fetchAPI<import('./types').Market & { snapshots: any[] }>(`/markets/${id}`)
}

export async function getMarketStats() {
  return fetchAPI<import('./types').MarketStats>('/markets/stats/summary')
}

// Patterns
export async function getPatterns(params?: {
  pattern_type?: string
  market_id?: string
  min_score?: number
  status?: string
  limit?: number
  offset?: number
}) {
  const searchParams = new URLSearchParams()
  if (params?.pattern_type) searchParams.set('pattern_type', params.pattern_type)
  if (params?.market_id) searchParams.set('market_id', params.market_id)
  if (params?.min_score) searchParams.set('min_score', params.min_score.toString())
  if (params?.status) searchParams.set('status', params.status)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  return fetchAPI<{
    patterns: import('./types').Pattern[]
    total: number
    offset: number
    limit: number
  }>(`/patterns?${searchParams}`)
}

export async function getOpportunities(tier: string = 'basic', limit: number = 10) {
  return fetchAPI<{
    tier: string
    opportunities: import('./types').Opportunity[]
    total_available: number
  }>(`/patterns/opportunities?tier=${tier}&limit=${limit}`)
}

export async function getPatternStats() {
  return fetchAPI<import('./types').PatternStats>('/patterns/stats')
}

export async function triggerAnalysis() {
  return fetchAPI<{ status: string; result: any }>('/patterns/analyze', {
    method: 'POST',
  })
}

// Alerts
export async function getAlerts(tier: string = 'basic', limit: number = 10) {
  return fetchAPI<{
    tier: string
    alerts: import('./types').Alert[]
    count: number
  }>(`/patterns/alerts?tier=${tier}&limit=${limit}`)
}

// Collection
export async function triggerCollection() {
  return fetchAPI<{ status: string; result: any }>('/collect', {
    method: 'POST',
  })
}

// AI Insights
export async function getAIInsights(params?: { category?: string; limit?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.category) searchParams.set('category', params.category)
  if (params?.limit) searchParams.set('limit', params.limit.toString())

  return fetchAPI<import('./types').AIInsightsResponse>(`/insights/ai?${searchParams}`)
}

export async function getInsightStats() {
  return fetchAPI<import('./types').InsightStats>('/insights/stats')
}

export async function getDailyDigest() {
  return fetchAPI<{ digest: import('./types').DailyDigest | null; tier: string; message?: string }>('/insights/digest')
}

// Cross-Platform
export async function getCrossPlatformMatches(params?: { limit?: number; min_volume?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.min_volume) searchParams.set('min_volume', params.min_volume.toString())

  return fetchAPI<{
    matches: import('./types').CrossPlatformMatch[]
    total: number
    total_volume: number
  }>(`/cross-platform/matches?${searchParams}`)
}

export async function getCrossPlatformSpotlight(matchId: string) {
  return fetchAPI<import('./types').CrossPlatformSpotlight>(`/cross-platform/spotlight/${matchId}`)
}

export async function getCrossPlatformSpotlights(limit: number = 10) {
  return fetchAPI<{
    spotlights: import('./types').CrossPlatformSpotlight[]
    total: number
  }>(`/cross-platform/spotlights?limit=${limit}`)
}

export async function getCrossPlatformStats() {
  return fetchAPI<{
    total_matches: number
    total_volume: number
    avg_price_gap: number
    categories: Record<string, number>
  }>('/cross-platform/stats')
}
