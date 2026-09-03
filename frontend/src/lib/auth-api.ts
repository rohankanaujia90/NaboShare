import { apiRequest } from './api'

export type User = {
  id: string
  full_name: string
  email: string
  phone: string | null
  nabo_score: number
  created_at: string
}

type TokenResponse = {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export type RegisterData = {
  full_name: string
  email: string
  phone: string | null
  password: string
}

export function registerUser(data: RegisterData): Promise<User> {
  return apiRequest<User>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function loginUser(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getCurrentUser(token: string): Promise<User> {
  return apiRequest<User>('/api/v1/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
}
