import { useEffect, useState, type PropsWithChildren } from 'react'

import { getCurrentUser, loginUser, registerUser } from '../lib/auth-api'
import type { RegisterData, User } from '../lib/auth-api'
import { AuthContext } from './auth-context'

const TOKEN_STORAGE_KEY = 'naboshare_access_token'

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!token) {
      setIsLoading(false)
      return
    }
    setAccessToken(token)

    let isActive = true
    void getCurrentUser(token)
      .then((currentUser) => {
        if (isActive) setUser(currentUser)
      })
      .catch(() => {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY)
        if (isActive) setAccessToken(null)
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
    setAccessToken(token)
    setUser(currentUser)
  }

  async function register(data: RegisterData) {
    await registerUser(data)
    await login(data.email, data.password)
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    setAccessToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, accessToken, isLoading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}
