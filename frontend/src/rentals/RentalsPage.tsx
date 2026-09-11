import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { NaboScoreBadge } from '../components/NaboScoreBadge'
import { money } from '../lib/items-api'
import {
  rentalActions,
  rentalStatuses,
  type Rental,
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

function RentalFeedback({
  rental,
  userId,
  state,
}: {
  rental: Rental
  userId: string
  state: ReturnType<typeof useRentals>
}) {
  const [rating, setRating] = useState(5)
  const owner = rental.owner_id === userId
  return (
    <div className="mt-4 flex flex-wrap items-end gap-3 border-t pt-4">
      {rental.status === 'RETURNED' && !rental.viewer_has_rated && (
        <>
          <label className="text-sm font-semibold">
            Rate your neighbour
            <select
              aria-label="Rating"
              value={rating}
              onChange={(event) => setRating(Number(event.target.value))}
              className="ml-2 rounded-lg border p-2"
            >
              {[5, 4, 3, 2, 1].map((value) => (
                <option key={value} value={value}>
                  {value} stars
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={!!state.busy}
            onClick={() => void state.rate(rental.id, rating)}
            className="rounded-lg bg-emerald-800 px-4 py-2 text-sm font-bold text-white"
          >
            Submit rating
          </button>
        </>
      )}
      {owner &&
        ['ACTIVE', 'RETURNED'].includes(rental.status) &&
        !rental.damage_reported && (
          <button
            disabled={!!state.busy}
            onClick={() => void state.reportDamage(rental.id)}
            className="rounded-lg border border-red-200 px-4 py-2 text-sm font-bold text-red-700"
          >
            Report damaged item
          </button>
        )}
    </div>
  )
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
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="mb-2 text-xs font-bold uppercase text-slate-500">
                      Borrower
                    </p>
                    <NaboScoreBadge
                      id={rental.borrower.id}
                      name={rental.borrower.full_name}
                      score={rental.borrower.nabo_score}
                      label={rental.borrower.nabo_label}
                    />
                  </div>
                  <div>
                    <p className="mb-2 text-xs font-bold uppercase text-slate-500">
                      Owner
                    </p>
                    <NaboScoreBadge
                      id={rental.owner.id}
                      name={rental.owner.full_name}
                      score={rental.owner.nabo_score}
                      label={rental.owner.nabo_label}
                    />
                  </div>
                </div>
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
                <RentalFeedback
                  rental={rental}
                  userId={user?.id ?? ''}
                  state={state}
                />
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
