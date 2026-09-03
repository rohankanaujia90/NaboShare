import { useEffect, useState, type PropsWithChildren } from 'react'

import { getCurrentUser, loginUser, registerUser } from '../lib/auth-api'
import type { RegisterData, User } from '../lib/auth-api'
import { AuthContext } from './auth-context'

const TOKEN_STORAGE_KEY = 'naboshare_access_token'

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!token) {
      setIsLoading(false)
      return
    }

    let isActive = true
    void getCurrentUser(token)
      .then((currentUser) => {
        if (isActive) setUser(currentUser)
      })
      .catch(() => {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY)
      })
      .finally(() => {
        if (isActive) setIsLoading(false)
      })

    return () => {
      isActive = false
    }
  }, [])

  async function login(email: string, password: string) {
    const { access_token: token } = await loginUser(email, password)
    const currentUser = await getCurrentUser(token)
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
    setUser(currentUser)
  }

  async function register(data: RegisterData) {
    await registerUser(data)
    await login(data.email, data.password)
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
