import { apiRequest } from './api'

export type User = {
  id: string
  full_name: string
  email: string
  phone: string | null
  nabo_score: number
  nabo_label: string
  created_at: string
}

export type PublicUser = Pick<
  User,
  'id' | 'full_name' | 'nabo_score' | 'nabo_label' | 'created_at'
>

export function getUserProfile(token: string, id: string): Promise<PublicUser> {
  return apiRequest<PublicUser>(`/api/v1/users/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
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
