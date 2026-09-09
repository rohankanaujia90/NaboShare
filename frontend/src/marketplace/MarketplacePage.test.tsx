import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MarketplacePage } from './MarketplacePage'

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ accessToken: 'test-token' }),
}))

describe('Marketplace', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })
  it('shows an empty result and sends selected filters with authorization', async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ items: [], total: 0 }), {
          status: 200,
        }),
      ),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(
      <MemoryRouter>
        <MarketplacePage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('No items found')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tools' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v1/items?category=Tools',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer test-token',
          },
        }),
      ),
    )
    fireEvent.change(screen.getByLabelText('Search items'), {
      target: { value: 'drill' },
    })
    await waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        '/api/v1/items?category=Tools&search=drill',
        expect.anything(),
      ),
    )
  })
  it('renders a product card linked to its detail page', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            total: 1,
            items: [
              {
                id: 'item-1',
                title: 'Cordless drill',
                category: 'Tools',
                image_url: null,
                availability: true,
                rental_price_per_day: '125.50',
                security_deposit: '500.00',
              },
            ],
          }),
          { status: 200 },
        ),
      ),
    )
    render(
      <MemoryRouter>
        <MarketplacePage />
      </MemoryRouter>,
    )
    const card = await screen.findByRole('link', { name: /Cordless drill/ })
    expect(card).toHaveAttribute('href', '/items/item-1')
    expect(screen.getByText('₹125.50')).toBeInTheDocument()
  })
})
