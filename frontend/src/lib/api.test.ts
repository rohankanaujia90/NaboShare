import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, apiRequest, apiUrl } from './api'

describe('apiUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('creates a same-origin API path by default', () => {
    expect(apiUrl('/api/v1/health')).toBe('/api/v1/health')
  })

  it('surfaces API error details', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: 'Incorrect email or password' }),
          {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    )

    await expect(apiRequest('/api/v1/auth/login')).rejects.toEqual(
      new ApiError('Incorrect email or password', 401),
    )
  })
})
