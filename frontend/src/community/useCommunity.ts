import { useEffect, useState } from 'react'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../lib/api'
import {
  createCommunity,
  getMyCommunity,
  joinCommunity,
  type Community,
  type CreateCommunityData,
} from '../lib/community-api'

export function useCommunity() {
  const { accessToken } = useAuth()
  const [community, setCommunity] = useState<Community | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!accessToken) {
      setIsLoading(false)
      return
    }

    let isActive = true
    void getMyCommunity(accessToken)
      .then((result) => {
        if (isActive) setCommunity(result)
      })
      .catch((caughtError: unknown) => {
        const isNotJoined =
          caughtError instanceof ApiError && caughtError.status === 404
        if (isActive && !isNotJoined) {
          setError(
            caughtError instanceof ApiError
              ? caughtError.message
              : 'Unable to load your community.',
          )
        }
      })
      .finally(() => {
        if (isActive) setIsLoading(false)
      })

    return () => {
      isActive = false
    }
  }, [accessToken])

  async function create(data: CreateCommunityData) {
    if (!accessToken) throw new Error('Authentication required')
    setError('')
    try {
      setCommunity(await createCommunity(accessToken, data))
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : 'Unable to create the community.',
      )
      throw caughtError
    }
  }

  async function join(inviteCode: string) {
    if (!accessToken) throw new Error('Authentication required')
    setError('')
    try {
      setCommunity(await joinCommunity(accessToken, inviteCode))
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : 'Unable to join the community.',
      )
      throw caughtError
    }
  }

  return { community, isLoading, error, create, join }
}
