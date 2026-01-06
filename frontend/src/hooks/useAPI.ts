import useSWR from 'swr'
import * as api from '@/lib/api'

const fetcher = async <T>(key: string): Promise<T> => {
  // Parse key to determine API call
  const [endpoint, ...params] = key.split('|')

  switch (endpoint) {
    case 'markets':
      return api.getMarkets(params[0] ? JSON.parse(params[0]) : undefined) as Promise<T>
    case 'market':
      return api.getMarket(params[0]) as Promise<T>
    case 'marketDetail':
      return api.getMarketDetail(params[0]) as Promise<T>
    case 'marketStats':
      return api.getMarketStats() as Promise<T>
    case 'patterns':
      return api.getPatterns(params[0] ? JSON.parse(params[0]) : undefined) as Promise<T>
    case 'opportunities':
      return api.getOpportunities(params[0], parseInt(params[1] || '10')) as Promise<T>
    case 'patternStats':
      return api.getPatternStats() as Promise<T>
    case 'alerts':
      return api.getAlerts(params[0], parseInt(params[1] || '10')) as Promise<T>
    case 'aiInsights':
      return api.getAIInsights(params[0] ? JSON.parse(params[0]) : undefined) as Promise<T>
    case 'insightDetail':
      return api.getInsightDetail(params[0]) as Promise<T>
    case 'insightStats':
      return api.getInsightStats() as Promise<T>
    case 'dailyDigest':
      return api.getDailyDigest() as Promise<T>
    case 'crossPlatformMatches':
      return api.getCrossPlatformMatches(params[0] ? JSON.parse(params[0]) : undefined) as Promise<T>
    case 'crossPlatformSpotlight':
      return api.getCrossPlatformSpotlight(params[0]) as Promise<T>
    case 'crossPlatformSpotlights':
      return api.getCrossPlatformSpotlights(parseInt(params[0] || '10')) as Promise<T>
    case 'crossPlatformStats':
      return api.getCrossPlatformStats() as Promise<T>
    default:
      throw new Error(`Unknown endpoint: ${endpoint}`)
  }
}

export function useMarkets(params?: Parameters<typeof api.getMarkets>[0]) {
  return useSWR(
    ['markets', params ? JSON.stringify(params) : ''].join('|'),
    fetcher<Awaited<ReturnType<typeof api.getMarkets>>>,
    { refreshInterval: 60000 }
  )
}

export function useMarket(id: string) {
  return useSWR(
    id ? `market|${id}` : null,
    fetcher<Awaited<ReturnType<typeof api.getMarket>>>
  )
}

export function useMarketStats() {
  return useSWR(
    'marketStats',
    fetcher<Awaited<ReturnType<typeof api.getMarketStats>>>,
    { refreshInterval: 30000 }
  )
}

export function usePatterns(params?: Parameters<typeof api.getPatterns>[0]) {
  return useSWR(
    ['patterns', params ? JSON.stringify(params) : ''].join('|'),
    fetcher<Awaited<ReturnType<typeof api.getPatterns>>>,
    { refreshInterval: 30000 }
  )
}

export function useOpportunities(tier: string = 'basic', limit: number = 10) {
  return useSWR(
    `opportunities|${tier}|${limit}`,
    fetcher<Awaited<ReturnType<typeof api.getOpportunities>>>,
    { refreshInterval: 30000 }
  )
}

export function usePatternStats() {
  return useSWR(
    'patternStats',
    fetcher<Awaited<ReturnType<typeof api.getPatternStats>>>,
    { refreshInterval: 30000 }
  )
}

export function useAlerts(tier: string = 'basic', limit: number = 10) {
  return useSWR(
    `alerts|${tier}|${limit}`,
    fetcher<Awaited<ReturnType<typeof api.getAlerts>>>,
    { refreshInterval: 30000 }
  )
}

// AI Insights hooks
export function useAIInsights(params?: Parameters<typeof api.getAIInsights>[0]) {
  return useSWR(
    ['aiInsights', params ? JSON.stringify(params) : ''].join('|'),
    fetcher<Awaited<ReturnType<typeof api.getAIInsights>>>,
    { refreshInterval: 60000 }
  )
}

export function useInsightStats() {
  return useSWR(
    'insightStats',
    fetcher<Awaited<ReturnType<typeof api.getInsightStats>>>,
    { refreshInterval: 60000 }
  )
}

export function useDailyDigest() {
  return useSWR(
    'dailyDigest',
    fetcher<Awaited<ReturnType<typeof api.getDailyDigest>>>,
    { refreshInterval: 300000 } // 5 minutes
  )
}

// Cross-Platform hooks
export function useCrossPlatformMatches(params?: Parameters<typeof api.getCrossPlatformMatches>[0]) {
  return useSWR(
    ['crossPlatformMatches', params ? JSON.stringify(params) : ''].join('|'),
    fetcher<Awaited<ReturnType<typeof api.getCrossPlatformMatches>>>,
    { refreshInterval: 60000 }
  )
}

export function useCrossPlatformSpotlight(matchId: string | null) {
  return useSWR(
    matchId ? `crossPlatformSpotlight|${matchId}` : null,
    fetcher<Awaited<ReturnType<typeof api.getCrossPlatformSpotlight>>>
  )
}

export function useCrossPlatformSpotlights(limit: number = 10) {
  return useSWR(
    `crossPlatformSpotlights|${limit}`,
    fetcher<Awaited<ReturnType<typeof api.getCrossPlatformSpotlights>>>,
    { refreshInterval: 60000 }
  )
}

export function useCrossPlatformStats() {
  return useSWR(
    'crossPlatformStats',
    fetcher<Awaited<ReturnType<typeof api.getCrossPlatformStats>>>,
    { refreshInterval: 60000 }
  )
}

// Detail page hooks
export function useInsightDetail(id: string | null) {
  return useSWR(
    id ? `insightDetail|${id}` : null,
    fetcher<Awaited<ReturnType<typeof api.getInsightDetail>>>
  )
}

export function useMarketDetail(id: string | null) {
  return useSWR(
    id ? `marketDetail|${id}` : null,
    fetcher<Awaited<ReturnType<typeof api.getMarketDetail>>>
  )
}

// Admin hooks
export function useAdminStats() {
  return useSWR(
    'adminStats',
    () => api.getAdminStats(),
    { refreshInterval: 60000 }
  )
}

export function useAdminUsers(params?: { search?: string; tier?: string; page?: number }) {
  return useSWR(
    ['adminUsers', params?.search || '', params?.tier || '', params?.page || 1].join('|'),
    () => api.getAdminUsers(params),
    { refreshInterval: 30000 }
  )
}

export function useAdminUser(userId: string | null) {
  return useSWR(
    userId ? `adminUser|${userId}` : null,
    () => userId ? api.getAdminUser(userId) : null
  )
}

export function useAdminHealth() {
  return useSWR(
    'adminHealth',
    () => api.getAdminHealth(),
    { refreshInterval: 30000 }
  )
}
