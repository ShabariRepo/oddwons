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

export async function getInsightDetail(id: string) {
  return fetchAPI<import('./types').InsightDetailResponse>(`/insights/ai/${id}`)
}

export async function getMarketDetail(id: string) {
  return fetchAPI<import('./types').MarketDetailResponse>(`/markets/${id}`)
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

// Admin APIs
export interface AdminStats {
  users: {
    total: number
    new_24h: number
    new_7d: number
    trialing: number
  }
  tiers: Record<string, number>
  revenue: {
    paid_users: number
    estimated_mrr: number
  }
  content: {
    total_markets: number
    active_insights: number
  }
}

export interface AdminUser {
  id: string
  email: string
  name: string | null
  subscription_tier: string
  subscription_status: string | null
  stripe_customer_id: string | null
  trial_end: string | null
  created_at: string | null
  last_login: string | null
  is_admin: boolean
}

export async function getAdminStats() {
  return fetchAPI<AdminStats>('/admin/stats')
}

export async function getAdminUsers(params?: { search?: string; tier?: string; page?: number; page_size?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.search) searchParams.set('search', params.search)
  if (params?.tier) searchParams.set('tier', params.tier)
  if (params?.page) searchParams.set('page', params.page.toString())
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString())

  return fetchAPI<{
    users: AdminUser[]
    total: number
    page: number
    page_size: number
  }>(`/admin/users?${searchParams}`)
}

export async function getAdminUser(userId: string) {
  return fetchAPI<{
    user: AdminUser & {
      stripe_subscription_id: string | null
      subscription_end: string | null
    }
    stripe_subscription: any | null
  }>(`/admin/users/${userId}`)
}

export async function syncUserSubscription(userId: string) {
  return fetchAPI<{
    message: string
    synced: boolean
    tier?: string
    status?: string
  }>(`/admin/users/${userId}/sync-subscription`, { method: 'POST' })
}

export async function changeUserTier(userId: string, tier: string) {
  return fetchAPI<{
    message: string
    user_id: string
    old_tier: string
    new_tier: string
  }>(`/admin/users/${userId}/change-tier?tier=${tier}`, { method: 'POST' })
}

export async function grantUserTrial(userId: string, days: number = 7) {
  return fetchAPI<{
    message: string
    trial_end: string
  }>(`/admin/users/${userId}/grant-trial?days=${days}`, { method: 'POST' })
}

export async function getAdminHealth() {
  return fetchAPI<{
    database: string
    redis: string
    stripe: string
  }>('/admin/health')
}

// ============ X BOT ADMIN ============

export interface XPost {
  id: string
  tweet_id: string | null
  tweet_url: string | null
  post_type: string
  status: string
  content: string
  has_image: boolean
  image_url: string | null
  market_data: any | null
  insight_ids: string[] | null
  market_ids: string[] | null
  error_message: string | null
  created_at: string | null
  posted_at: string | null
}

export interface XBotSettings {
  enabled: boolean
  morning_movers_enabled: boolean
  platform_comparison_enabled: boolean
  market_highlight_enabled: boolean
  weekly_recap_enabled: boolean
  promo_enabled: boolean
  max_posts_per_day: number
  updated_at: string | null
  updated_by: string | null
}

export async function getXPosts(params?: { status?: string; post_type?: string; page?: number; page_size?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.post_type) searchParams.set('post_type', params.post_type)
  if (params?.page) searchParams.set('page', params.page.toString())
  if (params?.page_size) searchParams.set('page_size', params.page_size.toString())

  return fetchAPI<{
    posts: XPost[]
    total: number
    page: number
    page_size: number
  }>(`/admin/x-posts?${searchParams}`)
}

export async function getXPostStats() {
  return fetchAPI<{
    totals: { total: number; posted: number; failed: number }
    recent: { last_24h: number; last_7d: number }
    by_type: Record<string, number>
    bot_enabled: boolean
  }>('/admin/x-posts/stats')
}

export async function getXBotSettings() {
  return fetchAPI<{ settings: XBotSettings }>('/admin/x-bot/settings')
}

export async function toggleXBot(enabled: boolean) {
  return fetchAPI<{ message: string; settings: XBotSettings }>(
    `/admin/x-bot/toggle?enabled=${enabled}`,
    { method: 'POST' }
  )
}

export async function toggleXPostType(postType: string, enabled: boolean) {
  return fetchAPI<{ message: string; settings: XBotSettings }>(
    `/admin/x-bot/toggle-post-type?post_type=${postType}&enabled=${enabled}`,
    { method: 'POST' }
  )
}

export async function triggerXPost(postType: string) {
  return fetchAPI<{ message: string; result: any }>(
    `/admin/x-bot/post-now?post_type=${postType}`,
    { method: 'POST' }
  )
}
