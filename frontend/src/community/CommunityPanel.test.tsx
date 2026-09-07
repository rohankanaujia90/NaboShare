import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextValue } from '../auth/auth-context'
import { CommunityPanel } from './CommunityPanel'

const authValue: AuthContextValue = {
  user: {
    id: 'user-1',
    full_name: 'Rohan Kanaujia',
    email: 'rohan@example.com',
    phone: null,
    nabo_score: 100,
    created_at: '2026-09-07T00:00:00Z',
  },
  accessToken: 'test-token',
  isLoading: false,
  login: () => Promise.resolve(),
  register: () => Promise.resolve(),
  logout: () => undefined,
}

describe('CommunityPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lets an unassigned user join with an invite code', async () => {
    const community = {
      id: 'community-1',
      name: 'North Campus',
      type: 'college',
      city: 'Delhi',
      invite_code: 'ABCD2345',
      created_at: '2026-09-07T00:00:00Z',
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ detail: 'You have not joined a community' }),
          {
            status: 404,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(community), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(
      <AuthContext.Provider value={authValue}>
        <CommunityPanel />
      </AuthContext.Provider>,
    )

    const input = await screen.findByLabelText('Invite code')
    fireEvent.change(input, { target: { value: 'abcd2345' } })
    fireEvent.click(screen.getByRole('button', { name: 'Join community' }))

    expect(
      await screen.findByRole('heading', { name: 'North Campus' }),
    ).toBeInTheDocument()
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/v1/communities/join',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ invite_code: 'ABCD2345' }),
      }),
    )
  })
})
