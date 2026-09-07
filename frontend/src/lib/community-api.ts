import { apiRequest } from './api'

export type CommunityType =
  'college' | 'hostel' | 'apartment_society' | 'corporate_campus'

export type Community = {
  id: string
  name: string
  type: CommunityType
  city: string
  invite_code: string
  created_at: string
}

export type CreateCommunityData = {
  name: string
  type: CommunityType
  city: string
}

function authenticatedHeaders(token: string) {
  return { Authorization: `Bearer ${token}` }
}

export function getMyCommunity(token: string): Promise<Community> {
  return apiRequest<Community>('/api/v1/communities/me', {
    headers: authenticatedHeaders(token),
  })
}

export function createCommunity(
  token: string,
  data: CreateCommunityData,
): Promise<Community> {
  return apiRequest<Community>('/api/v1/communities', {
    method: 'POST',
    headers: authenticatedHeaders(token),
    body: JSON.stringify(data),
  })
}

export function joinCommunity(
  token: string,
  inviteCode: string,
): Promise<Community> {
  return apiRequest<Community>('/api/v1/communities/join', {
    method: 'POST',
    headers: authenticatedHeaders(token),
    body: JSON.stringify({ invite_code: inviteCode }),
  })
}
