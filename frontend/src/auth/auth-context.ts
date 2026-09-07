import { createContext } from 'react'

import type { RegisterData, User } from '../lib/auth-api'

export type AuthContextValue = {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
