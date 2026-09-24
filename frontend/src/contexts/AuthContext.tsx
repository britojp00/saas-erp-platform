import { useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { createContext } from 'react'
import { api, setAuthToken, setUnauthorizedHandler } from '../services/api'
import type { LoginRequest, TokenResponse, UserResponse } from '../types/auth'

const TOKEN_STORAGE_KEY = 'saas_erp.access_token'

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  user: UserResponse | null
  status: AuthStatus
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function readStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

function storeToken(token: string | null): void {
  if (token === null) {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY)
  } else {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  const clearSession = useCallback(() => {
    storeToken(null)
    setAuthToken(null)
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  useEffect(() => {
    let active = true
    setUnauthorizedHandler(clearSession)

    const token = readStoredToken()
    if (token === null) {
      setStatus('unauthenticated')
      return () => {
        active = false
        setUnauthorizedHandler(null)
      }
    }

    setAuthToken(token)
    api
      .get<UserResponse>('/api/v1/auth/me')
      .then((me) => {
        if (!active) return
        setUser(me)
        setStatus('authenticated')
      })
      .catch(() => {
        if (!active) return
        clearSession()
      })

    return () => {
      active = false
      setUnauthorizedHandler(null)
    }
  }, [clearSession])

  const login = useCallback(async (credentials: LoginRequest) => {
    const tokenResponse = await api.post<TokenResponse>(
      '/api/v1/auth/login',
      credentials,
    )
    storeToken(tokenResponse.access_token)
    setAuthToken(tokenResponse.access_token)
    const me = await api.get<UserResponse>('/api/v1/auth/me')
    setUser(me)
    setStatus('authenticated')
  }, [])

  const logout = useCallback(() => {
    clearSession()
  }, [clearSession])

  const value = useMemo(
    () => ({ user, status, login, logout }),
    [user, status, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }
  return context
}
