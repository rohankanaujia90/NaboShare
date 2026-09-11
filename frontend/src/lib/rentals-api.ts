import { apiRequest } from './api'

export const rentalStatuses = [
  'PENDING',
  'ACCEPTED',
  'REJECTED',
  'ACTIVE',
  'RETURNED',
  'CANCELLED',
] as const
export type RentalStatus = (typeof rentalStatuses)[number]
export type RentalAction = 'accept' | 'reject' | 'cancel' | 'start' | 'return'
export type Rental = {
  id: string
  item_id: string
  borrower_id: string
  owner_id: string
  start_date: string
  end_date: string
  rental_amount: string
  platform_fee: string
  security_deposit: string
  status: RentalStatus
  created_at: string
  borrower: RentalParty
  owner: RentalParty
  viewer_has_rated: boolean
  damage_reported: boolean
}
export type RentalParty = {
  id: string
  full_name: string
  nabo_score: number
  nabo_label: string
}
export type RentalPage = { rentals: Rental[]; total: number }
export const utcToday = () => new Date().toISOString().slice(0, 10)
export function estimateRental(
  start: string,
  end: string,
  daily: string,
  deposit: string,
) {
  const days = (Date.parse(end) - Date.parse(start)) / 86400000
  if (!Number.isInteger(days) || days < 1 || days > 365) return null
  const cents = (value: string) => Math.round(Number(value) * 100)
  const amount = days * cents(daily)
  return {
    days,
    amount: (amount / 100).toFixed(2),
    fee: (Math.round(amount / 10) / 100).toFixed(2),
    total: ((amount + cents(deposit)) / 100).toFixed(2),
  }
}
export function rentalActions(
  rental: Rental,
  userId: string,
  today = utcToday(),
): RentalAction[] {
  const owner = rental.owner_id === userId
  if (!owner && rental.borrower_id !== userId) return []
  if (rental.status === 'PENDING')
    return owner ? ['accept', 'reject', 'cancel'] : ['cancel']
  if (rental.status === 'ACCEPTED') {
    if (today < rental.start_date) return ['cancel']
    if (owner && today < rental.end_date) return ['start']
  }
  return owner && rental.status === 'ACTIVE' ? ['return'] : []
}
export function rentalRequest<T>(
  token: string,
  path = '',
  method = 'GET',
  data?: unknown,
  signal?: AbortSignal,
) {
  return apiRequest<T>(`/api/v1/rentals${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}` },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    signal,
  })
}
