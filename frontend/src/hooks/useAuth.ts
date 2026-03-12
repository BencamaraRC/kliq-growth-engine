import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { login as apiLogin } from '@/api/auth'

interface User {
  username: string
  name: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

export const AuthContext = createContext<AuthContextType | null>(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function useAuthState() {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('kliq_user')
    return stored ? JSON.parse(stored) : null
  })
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem('kliq_token')
  )

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password)
    localStorage.setItem('kliq_token', data.access_token)
    localStorage.setItem('kliq_user', JSON.stringify(data.user))
    setToken(data.access_token)
    setUser(data.user)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('kliq_token')
    localStorage.removeItem('kliq_user')
    setToken(null)
    setUser(null)
  }, [])

  // Sync across tabs
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === 'kliq_token' && !e.newValue) {
        setToken(null)
        setUser(null)
      }
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  return { user, token, login, logout, isAuthenticated: !!token }
}
