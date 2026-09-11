import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import {
  estimateRental,
  rentalActions,
  rentalRequest,
  type Rental,
} from '../lib/rentals-api'
import { RequestRentalForm } from './RequestRentalForm'
import { RentalsPage } from './RentalsPage'

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({
    accessToken: 'token',
    user: { id: 'owner' },
    refreshUser: vi.fn().mockResolvedValue(undefined),
  }),
}))
vi.mock('../lib/rentals-api', async (original) => ({
  ...(await original<typeof import('../lib/rentals-api')>()),
  rentalRequest: vi.fn(),
}))
const rental: Rental = {
  id: 'rental',
  item_id: 'item',
  owner_id: 'owner',
  borrower_id: 'borrower',
  start_date: '2099-01-10',
  end_date: '2099-01-12',
  rental_amount: '301.10',
  platform_fee: '30.11',
  security_deposit: '1000.00',
  status: 'PENDING',
  created_at: '',
  borrower: {
    id: 'borrower',
    full_name: 'Asha',
    nabo_score: 78,
    nabo_label: 'Good',
  },
  owner: {
    id: 'owner',
    full_name: 'Rohan',
    nabo_score: 95,
    nabo_label: 'Excellent',
  },
  viewer_has_rated: false,
  damage_reported: false,
}
afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})
describe('rental rules', () => {
  it('estimates exclusive dates and rounds commission to cents', () => {
    expect(
      estimateRental('2099-01-10', '2099-01-12', '150.55', '1000'),
    ).toEqual({ days: 2, amount: '301.10', fee: '30.11', total: '1301.10' })
    expect(estimateRental('2099-01-10', '2099-01-11', '0.05', '0')?.fee).toBe(
      '0.01',
    )
    expect(estimateRental('', '', '10', '0')).toBeNull()
    expect(estimateRental('2099-01-10', '2099-01-10', '10', '0')).toBeNull()
    expect(estimateRental('2099-01-10', '2100-01-12', '10', '0')).toBeNull()
  })
  it('shows only participant actions and respects pickup/cancellation dates', () => {
    expect(rentalActions(rental, 'borrower')).toEqual(['cancel'])
    expect(rentalActions(rental, 'stranger')).toEqual([])
    expect(rentalActions(rental, 'owner')).toEqual([
      'accept',
      'reject',
      'cancel',
    ])
    expect(
      rentalActions({ ...rental, status: 'ACCEPTED' }, 'owner', '2099-01-10'),
    ).toEqual(['start'])
    expect(
      rentalActions(
        { ...rental, status: 'ACCEPTED' },
        'borrower',
        '2099-01-10',
      ),
    ).toEqual([])
    expect(rentalActions({ ...rental, status: 'ACTIVE' }, 'owner')).toEqual([
      'return',
    ])
    expect(rentalActions({ ...rental, status: 'RETURNED' }, 'owner')).toEqual(
      [],
    )
  })
})
it('submits dates without client pricing and displays server conflicts before retry', async () => {
  vi.mocked(rentalRequest)
    .mockRejectedValueOnce(new Error('Already booked'))
    .mockResolvedValueOnce(rental)
  render(
    <MemoryRouter>
      <RequestRentalForm
        item={{
          id: 'item',
          owner_id: 'someone',
          community_id: 'community',
          title: 'Projector',
          description: 'Test',
          category: 'Electronics',
          rental_price_per_day: '150.55',
          security_deposit: '1000',
          replacement_value: '10000',
          availability: true,
          image_url: null,
          created_at: '',
        }}
      />
    </MemoryRouter>,
  )
  fireEvent.change(screen.getByLabelText('Pickup date'), {
    target: { value: '2099-01-10' },
  })
  fireEvent.change(screen.getByLabelText('Return date'), {
    target: { value: '2099-01-12' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Request to borrow' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Already booked')
  fireEvent.click(screen.getByRole('button', { name: 'Request to borrow' }))
  expect(
    await screen.findByRole('link', { name: 'View rentals' }),
  ).toBeInTheDocument()
  expect(rentalRequest).toHaveBeenCalledWith('token', '', 'POST', {
    item_id: 'item',
    start_date: '2099-01-10',
    end_date: '2099-01-12',
  })
})
it('loads lending requests and refreshes after accepting', async () => {
  vi.mocked(rentalRequest).mockImplementation((_token, path, method) =>
    Promise.resolve(
      method === 'POST'
        ? rental
        : {
            rentals: [
              {
                ...rental,
                status: path?.includes('role=owner') ? 'PENDING' : 'CANCELLED',
              },
            ],
            total: 1,
          },
    ),
  )
  render(
    <MemoryRouter>
      <RentalsPage />
    </MemoryRouter>,
  )
  await screen.findByText('CANCELLED')
  fireEvent.click(screen.getByRole('button', { name: 'Lending' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Accept request' }))
  await waitFor(() =>
    expect(rentalRequest).toHaveBeenCalledWith(
      'token',
      '/rental/accept',
      'POST',
      undefined,
    ),
  )
  await screen.findByRole('button', { name: 'Accept request' })
})

it('shows scores and submits post-return feedback', async () => {
  vi.mocked(rentalRequest).mockImplementation((_token, _path, method) =>
    Promise.resolve(
      method === 'POST'
        ? rental
        : { rentals: [{ ...rental, status: 'RETURNED' }], total: 1 },
    ),
  )
  render(
    <MemoryRouter>
      <RentalsPage />
    </MemoryRouter>,
  )
  expect(await screen.findByText('Excellent')).toBeInTheDocument()
  expect(screen.getByText('Good')).toBeInTheDocument()
  fireEvent.change(screen.getByLabelText('Rating'), { target: { value: '4' } })
  fireEvent.click(screen.getByRole('button', { name: 'Submit rating' }))
  await waitFor(() =>
    expect(rentalRequest).toHaveBeenCalledWith(
      'token',
      '/rental/rating',
      'POST',
      { rating: 4 },
    ),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Report damaged item' }))
  await waitFor(() =>
    expect(rentalRequest).toHaveBeenCalledWith(
      'token',
      '/rental/damage-dispute',
      'POST',
      undefined,
    ),
  )
})
