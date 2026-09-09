import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { money, type Item } from '../lib/items-api'
import { estimateRental, rentalRequest, utcToday } from '../lib/rentals-api'

export function RequestRentalForm({ item }: { item: Item }) {
  const { accessToken } = useAuth()
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const estimate = estimateRental(
    start,
    end,
    item.rental_price_per_day,
    item.security_deposit,
  )
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!accessToken || !estimate || busy) return
    setBusy(true)
    setError('')
    try {
      await rentalRequest(accessToken, '', 'POST', {
        item_id: item.id,
        start_date: start,
        end_date: end,
      })
      setSent(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to request rental')
    } finally {
      setBusy(false)
    }
  }
  if (sent)
    return (
      <div role="status" className="mt-8 rounded-2xl bg-emerald-100 p-6">
        Request sent! The owner will review your dates.{' '}
        <Link className="font-bold underline" to="/rentals">
          View rentals
        </Link>
      </div>
    )
  return (
    <form
      onSubmit={(event) => void submit(event)}
      className="mt-8 space-y-4 rounded-2xl border border-emerald-200 bg-white p-6"
    >
      <h2 className="text-xl font-bold">Borrow from your neighbour</h2>
      <p className="text-sm text-slate-600">
        Return date is exclusive. Dates use UTC. Requests do not reserve the
        item until accepted.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-semibold">
          Pickup date
          <input
            required
            type="date"
            min={utcToday()}
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="mt-2 block w-full min-w-0 rounded-lg border p-3"
          />
        </label>
        <label className="text-sm font-semibold">
          Return date
          <input
            required
            type="date"
            min={start || utcToday()}
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="mt-2 block w-full min-w-0 rounded-lg border p-3"
          />
        </label>
      </div>
      {start && end && !estimate && (
        <p role="alert">Choose a rental lasting 1–365 days.</p>
      )}
      {estimate && (
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt>Rental · {estimate.days} days</dt>
            <dd>{money(estimate.amount)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>10% commission (included)</dt>
            <dd>{money(estimate.fee)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Security deposit</dt>
            <dd>{money(item.security_deposit)}</dd>
          </div>
          <div className="flex justify-between border-t pt-2 font-bold">
            <dt>Rental + deposit</dt>
            <dd>{money(estimate.total)}</dd>
          </div>
        </dl>
      )}
      <p className="text-xs text-slate-500">
        Estimate only; the server confirms current pricing. No payment is
        collected by this MVP.
      </p>
      {error && (
        <p role="alert" className="text-red-700">
          {error}
        </p>
      )}
      <button
        disabled={!item.availability || !estimate || busy}
        className="w-full rounded-xl bg-emerald-800 p-3 font-bold text-white disabled:opacity-50"
      >
        {busy
          ? 'Sending…'
          : item.availability
            ? 'Request to borrow'
            : 'Item unavailable'}
      </button>
    </form>
  )
}
