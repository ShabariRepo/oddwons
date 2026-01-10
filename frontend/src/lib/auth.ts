const API_BASE = '/api/v1'

export interface User {
  id: string
  email: string
  name?: string
  is_active: boolean
  is_verified: boolean
  is_admin?: boolean
  subscription_tier?: 'basic' | 'premium' | 'pro'
  subscription_status: 'active' | 'canceled' | 'past_due' | 'trialing' | 'inactive'
  subscription_end?: string
  trial_end_date?: string
  trial_end?: string
  trial_start?: string
  created_at: string
}

export interface AuthToken {
  access_token: string
  token_type: string
  expires_in: number
}

const TOKEN_KEY = 'oddwons_token'

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

async function authFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...headers,
        ...options?.headers,
      },
    })
  } catch (err) {
    // Network error - backend unreachable
    throw new Error('Unable to connect to server. Please check your connection.')
  }

  if (res.status === 401) {
    removeToken()
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: `Request failed (${res.status})` }))
    throw new Error(error.detail || `Request failed (${res.status})`)
  }

  return res.json()
}

export async function register(email: string, password: string, name?: string): Promise<AuthToken> {
  const result = await authFetch<AuthToken>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  })
  setToken(result.access_token)
  return result
}

export async function login(email: string, password: string): Promise<AuthToken> {
  const result = await authFetch<AuthToken>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  setToken(result.access_token)
  return result
}

export async function logout(): Promise<void> {
  try {
    await authFetch('/auth/logout', { method: 'POST' })
  } catch {
    // Ignore errors
  }
  removeToken()
}

export async function getMe(): Promise<User> {
  return authFetch<User>('/auth/me')
}

export async function updateProfile(data: { name?: string; email?: string }): Promise<User> {
  return authFetch<User>('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await authFetch('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
}

// Billing
export interface SubscriptionInfo {
  tier: string
  status: string
  current_period_end?: string
  cancel_at_period_end: boolean
  trial_end?: string
}

export interface PriceInfo {
  tier: string
  price_id: string
  amount: number
  currency: string
  interval: string
  features: string[]
}

export async function getSubscription(): Promise<SubscriptionInfo> {
  return authFetch<SubscriptionInfo>('/billing/subscription')
}

export async function getPrices(): Promise<{ prices: PriceInfo[]; publishable_key: string }> {
  return authFetch('/billing/prices')
}

export async function createCheckout(tier: string): Promise<{ checkout_url: string }> {
  return authFetch<{ checkout_url: string }>(`/billing/checkout/${tier}`, {
    method: 'POST',
  })
}

export async function createPortal(): Promise<{ portal_url: string }> {
  return authFetch<{ portal_url: string }>('/billing/portal', {
    method: 'POST',
  })
}

export async function cancelSubscription(): Promise<void> {
  await authFetch('/billing/cancel', { method: 'POST' })
}

export interface SyncResult {
  synced: boolean
  message: string
  tier: string
  status: string
  current_period_end?: string
  cancel_at_period_end?: boolean
}

export async function syncSubscription(): Promise<SyncResult> {
  return authFetch<SyncResult>('/billing/sync', { method: 'POST' })
}
