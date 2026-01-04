'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, getMe, getToken, removeToken, isAuthenticated as checkAuth } from '@/lib/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  refreshUser: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isAuthenticated: false,
  refreshUser: async () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    if (!getToken()) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const userData = await getMe()
      setUser(userData)
    } catch {
      setUser(null)
      removeToken()
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    removeToken()
    setUser(null)
    window.location.href = '/login'
  }

  useEffect(() => {
    refreshUser()
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        refreshUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

export function useRequireAuth() {
  const { user, loading, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      window.location.href = '/login'
    }
  }, [loading, isAuthenticated])

  return { user, loading }
}
