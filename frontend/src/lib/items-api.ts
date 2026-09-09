import { apiRequest } from './api'

export const categories = [
  'Electronics',
  'Tools',
  'Travel',
  'Books',
  'Sports',
  'Events',
  'Camping',
  'Other',
] as const
export type Category = (typeof categories)[number]
export type ItemInput = {
  title: string
  description: string
  category: Category
  rental_price_per_day: string
  security_deposit: string
  replacement_value: string
  image_url: string | null
  availability: boolean
}
export type Item = ItemInput & {
  id: string
  owner_id: string
  community_id: string
  created_at: string
}
export type ItemPage = { items: Item[]; total: number }
export const money = (value: string) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(Number(value))
export function itemRequest<T>(
  token: string,
  path = '',
  method = 'GET',
  data?: unknown,
  signal?: AbortSignal,
) {
  return apiRequest<T>(`/api/v1/items${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}` },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    signal,
  })
}
