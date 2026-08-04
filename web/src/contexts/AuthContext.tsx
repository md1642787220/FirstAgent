import { createContext, useContext, useState, type ReactNode } from 'react'

interface AuthUser {
  token: string
  username: string
  expiresAt: number
}

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (user: AuthUser) => void
  logout: () => void
}

const STORAGE_KEY = 'xg-auth'

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
})

function loadUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthUser
    // 过期则清除
    if (!parsed.expiresAt || parsed.expiresAt < Date.now() / 1000) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => loadUser())

  const login = (u: AuthUser) => {
    setUser(u)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u))
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
