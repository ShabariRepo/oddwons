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
