import { useEffect, useState } from 'react'
import { useAuth } from '../auth/useAuth'
import {
  rentalRequest,
  type RentalAction,
  type RentalPage,
} from '../lib/rentals-api'

export function useRentals() {
  const { accessToken, refreshUser } = useAuth()
  const [role, setRole] = useState('borrower')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)
  const [revision, setRevision] = useState(0)
  const [data, setData] = useState<RentalPage>({ rentals: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  useEffect(() => {
    if (!accessToken) return
    const controller = new AbortController()
    setLoading(true)
    setError('')
    const query = new URLSearchParams({
      role,
      limit: '12',
      offset: String(offset),
    })
    if (status) query.set('status', status)
    void rentalRequest<RentalPage>(
      accessToken,
      `?${query}`,
      'GET',
      undefined,
      controller.signal,
    )
      .then((value) => {
        if (!controller.signal.aborted) setData(value)
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted)
          setError(
            err instanceof Error ? err.message : 'Unable to load rentals',
          )
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [accessToken, role, status, offset, revision])
  async function mutate(id: string, path: string, body?: unknown) {
    if (!accessToken || busy) return
    setBusy(id)
    setError('')
    try {
      await rentalRequest(accessToken, `/${id}/${path}`, 'POST', body)
      await refreshUser()
      setRevision((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update rental')
    } finally {
      setBusy('')
    }
  }
  return {
    data,
    loading,
    error,
    busy,
    act: (id: string, action: RentalAction) => mutate(id, action),
    rate: (id: string, rating: number) => mutate(id, 'rating', { rating }),
    reportDamage: (id: string) => mutate(id, 'damage-dispute'),
    role,
    status,
    offset,
    setOffset,
    changeRole: (value: string) => {
      setRole(value)
      setOffset(0)
    },
    changeStatus: (value: string) => {
      setStatus(value)
      setOffset(0)
    },
    retry: () => setRevision((value) => value + 1),
  }
}
