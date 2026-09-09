import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { itemRequest, money, type Item } from '../lib/items-api'
import { ItemImage } from './ProductCard'
import { RequestRentalForm } from '../rentals/RequestRentalForm'

export function ItemDetailsPage() {
  const { id } = useParams()
  const { accessToken, user } = useAuth()
  const navigate = useNavigate()
  const [item, setItem] = useState<Item | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  useEffect(() => {
    if (!accessToken || !id) return
    let active = true
    setLoading(true)
    setError('')
    setItem(null)
    void itemRequest<Item>(accessToken, `/${id}`)
      .then((data) => {
        if (active) setItem(data)
      })
      .catch((err: unknown) => {
        if (active)
          setError(err instanceof Error ? err.message : 'Unable to load item')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken, id])
  async function remove() {
    if (!accessToken || !id) return
    setDeleting(true)
    try {
      await itemRequest<void>(accessToken, `/${id}`, 'DELETE')
      void navigate('/marketplace')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete item')
      setDeleting(false)
    }
  }
  return (
    <section className="mx-auto max-w-6xl px-5 py-8">
      <Link to="/marketplace" className="text-sm text-emerald-700">
        ← Back to marketplace
      </Link>
      {loading && (
        <p className="mt-8" role="status">
          Loading item…
        </p>
      )}
      {error && (
        <p role="alert" className="mt-6 rounded-xl bg-red-50 p-4 text-red-800">
          {error}
        </p>
      )}
      {item && (
        <div className="mt-8 grid gap-10 lg:grid-cols-2">
          <div className="aspect-square overflow-hidden rounded-[2rem]">
            <ItemImage key={item.id + item.image_url} item={item} />
          </div>
          <div>
            <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">
              {item.category}
            </p>
            <h1 className="mt-3 text-4xl font-black tracking-tight">
              {item.title}
            </h1>
            <span className="mt-4 inline-block rounded-full bg-emerald-100 px-4 py-2 text-sm font-bold text-emerald-900">
              {item.availability
                ? 'Available to rent'
                : 'Currently unavailable'}
            </span>
            <p className="mt-8 text-4xl font-black">
              {money(item.rental_price_per_day)}
              <span className="text-base font-normal text-slate-500">
                {' '}
                / day
              </span>
            </p>
            <dl className="mt-6 grid grid-cols-2 gap-4 rounded-2xl bg-white p-5">
              <div>
                <dt className="text-sm text-slate-500">Security deposit</dt>
                <dd className="mt-1 font-bold">
                  {money(item.security_deposit)}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-slate-500">Replacement value</dt>
                <dd className="mt-1 font-bold">
                  {money(item.replacement_value)}
                </dd>
              </div>
            </dl>
            <h2 className="mt-8 text-xl font-bold">About this item</h2>
            <p className="mt-3 whitespace-pre-wrap break-words leading-7 text-slate-600">
              {item.description}
            </p>
            {user?.id === item.owner_id && (
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  to={`/items/${item.id}/edit`}
                  className="rounded-xl bg-emerald-800 px-5 py-3 font-bold text-white"
                >
                  Edit listing
                </Link>
                <button
                  onClick={() => setConfirming(true)}
                  className="rounded-xl border border-red-200 px-5 py-3 text-red-700"
                >
                  Delete listing
                </button>
              </div>
            )}
            {user && user.id !== item.owner_id && (
              <RequestRentalForm key={item.id} item={item} />
            )}
            {confirming && (
              <div className="mt-4 rounded-xl border border-red-200 p-5">
                <p>Delete this listing? This cannot be undone.</p>
                <div className="mt-3 flex gap-4">
                  <button
                    disabled={deleting}
                    onClick={() => void remove()}
                    className="font-bold text-red-700"
                  >
                    {deleting ? 'Deleting…' : 'Confirm delete'}
                  </button>
                  <button
                    disabled={deleting}
                    onClick={() => setConfirming(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
