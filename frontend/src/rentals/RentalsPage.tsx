import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { money } from '../lib/items-api'
import {
  rentalActions,
  rentalStatuses,
  type RentalAction,
} from '../lib/rentals-api'
import { useRentals } from './useRentals'

const labels: Record<RentalAction, string> = {
  accept: 'Accept request',
  reject: 'Reject request',
  cancel: 'Cancel rental',
  start: 'Confirm pickup',
  return: 'Confirm return',
}
export function RentalsPage() {
  const { user } = useAuth()
  const state = useRentals()
  return (
    <section className="mx-auto max-w-6xl px-5 py-8">
      <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">
        Share more. Own less.
      </p>
      <h1 className="mt-3 text-4xl font-black">Your rentals</h1>
      <p className="mt-3 max-w-2xl text-slate-600">
        Keep track of requests, handovers and returns. Owners confirm pickup and
        return after the physical handover. Payments are not collected here.
      </p>
      <div className="my-8 flex flex-wrap items-center gap-3">
        {(['borrower', 'owner'] as const).map((role) => (
          <button
            key={role}
            aria-pressed={state.role === role}
            onClick={() => state.changeRole(role)}
            className={`rounded-full px-5 py-3 font-bold ${state.role === role ? 'bg-emerald-800 text-white' : 'border bg-white'}`}
          >
            {role === 'borrower' ? 'Borrowing' : 'Lending'}
          </button>
        ))}
        <label className="sm:ml-auto">
          Status{' '}
          <select
            className="ml-2 rounded-xl border bg-white p-3"
            value={state.status}
            onChange={(e) => state.changeStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            {rentalStatuses.map((status) => (
              <option key={status}>{status}</option>
            ))}
          </select>
        </label>
      </div>
      {state.error && (
        <div
          role="alert"
          className="mb-5 rounded-xl bg-red-50 p-4 text-red-800"
        >
          {state.error}{' '}
          <button className="underline" onClick={state.retry}>
            Retry
          </button>
        </div>
      )}
      {state.loading ? (
        <p role="status">Loading rentals…</p>
      ) : (
        <>
          {!state.error && !state.data.rentals.length && (
            <div className="rounded-2xl border border-dashed p-10 text-center">
              <h2 className="text-xl font-bold">No rentals yet</h2>
              <p className="mt-2 text-slate-600">
                Requests matching this view will appear here.
              </p>
              <Link
                to="/marketplace"
                className="mt-5 inline-block font-bold text-emerald-700"
              >
                Explore your community →
              </Link>
            </div>
          )}
          <div className="grid gap-5 md:grid-cols-2">
            {state.data.rentals.map((rental) => (
              <article
                key={rental.id}
                className="rounded-2xl border bg-white p-6 shadow-sm"
              >
                <div className="flex flex-wrap justify-between gap-3">
                  <Link
                    className="font-bold text-emerald-800 underline"
                    to={`/items/${rental.item_id}`}
                  >
                    View item →
                  </Link>
                  <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-bold">
                    {rental.status}
                  </span>
                </div>
                <h2 className="mt-5 text-lg font-bold">
                  {rental.start_date} → {rental.end_date}
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Return date exclusive · Ref {rental.id.slice(0, 8)}
                </p>
                <dl className="my-5 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt>Rental amount</dt>
                    <dd>{money(rental.rental_amount)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Commission (included)</dt>
                    <dd>{money(rental.platform_fee)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Security deposit</dt>
                    <dd>{money(rental.security_deposit)}</dd>
                  </div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  {rentalActions(rental, user?.id ?? '').map((action) => (
                    <button
                      key={action}
                      disabled={!!state.busy}
                      onClick={() => void state.act(rental.id, action)}
                      className="rounded-lg border border-emerald-200 px-4 py-3 text-sm font-bold text-emerald-800 hover:bg-emerald-50 disabled:opacity-50"
                    >
                      {state.busy === rental.id ? 'Updating…' : labels[action]}
                    </button>
                  ))}
                </div>
              </article>
            ))}
          </div>
          <div className="mt-6 flex items-center justify-between">
            <button
              disabled={!state.offset}
              onClick={() => state.setOffset(Math.max(0, state.offset - 12))}
              className="p-3 disabled:opacity-30"
            >
              ← Previous
            </button>
            <span className="text-sm">{state.data.total} rentals</span>
            <button
              disabled={state.offset + 12 >= state.data.total}
              onClick={() => state.setOffset(state.offset + 12)}
              className="p-3 disabled:opacity-30"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </section>
  )
}
