import { apiUrl } from './api'
import { describe, expect, it } from 'vitest'

describe('apiUrl', () => {
  it('creates a same-origin API path by default', () => {
    expect(apiUrl('/api/v1/health')).toBe('/api/v1/health')
  })
})
