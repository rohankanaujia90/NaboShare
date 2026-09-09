import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { categories, itemRequest, type ItemPage } from '../lib/items-api'
import { ProductCard } from './ProductCard'

export function MarketplacePage() {
  const { accessToken } = useAuth()
  const [params, setParams] = useSearchParams()
  const [result, setResult] = useState<ItemPage>({ items: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const query = params.toString()
  useEffect(() => {
    if (!accessToken) return
    const controller = new AbortController()
    setLoading(true)
    setError('')
    const timer = window.setTimeout(() => {
      void itemRequest<ItemPage>(
        accessToken,
        `?${query}`,
        'GET',
        undefined,
        controller.signal,
      )
        .then((data) => {
          if (!controller.signal.aborted) setResult(data)
        })
        .catch((err: unknown) => {
          if (!controller.signal.aborted)
            setError(
              err instanceof Error ? err.message : 'Unable to load items',
            )
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, 250)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [accessToken, query])
  function filter(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.delete('offset')
    setParams(next, { replace: true })
  }
  const offset = Number(params.get('offset') || 0)
  return (
    <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
      <div className="my-6 rounded-[2rem] bg-emerald-950 px-6 py-10 text-white sm:p-12">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">
          Closer to home. Lighter on your wallet.
        </p>
        <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-5xl">
          Good things, shared nearby.
        </h1>
        <p className="mt-4 max-w-xl text-emerald-100/80">
          Discover useful things to rent from people in your community.
        </p>
        <Link
          to="/items/new"
          className="mt-7 inline-block rounded-full bg-lime-300 px-6 py-3 font-bold text-emerald-950"
        >
          + List an item
        </Link>
      </div>
      <label className="block">
        <span className="sr-only">Search items</span>
        <input
          className="w-full rounded-2xl border border-stone-300 bg-white px-5 py-4"
          placeholder="Search projectors, tools, camping gear…"
          value={params.get('search') || ''}
          onChange={(e) => filter('search', e.target.value)}
          maxLength={160}
        />
      </label>
      <div
        className="my-5 flex gap-2 overflow-x-auto pb-2"
        aria-label="Categories"
      >
        {['', ...categories].map((category) => (
          <button
            key={category}
            type="button"
            aria-pressed={(params.get('category') || '') === category}
            onClick={() => filter('category', category)}
            className={`shrink-0 rounded-full border px-4 py-2 text-sm font-semibold ${(params.get('category') || '') === category ? 'border-emerald-900 bg-emerald-900 text-white' : 'border-stone-200 bg-white'}`}
          >
            {category || 'All items'}
          </button>
        ))}
      </div>
      <div className="mb-8 flex flex-wrap items-end gap-3">
        {[
          ['min_price', 'Min price'],
          ['max_price', 'Max price'],
        ].map(([key, label]) => (
          <label key={key} className="text-xs font-semibold text-slate-600">
            {label}
            <input
              className="mt-1 block w-28 rounded-xl border border-stone-300 p-3"
              aria-label={label}
              type="number"
              min="0"
              step="0.01"
              value={params.get(key) || ''}
              onChange={(e) => filter(key, e.target.value)}
            />
          </label>
        ))}
        <label className="text-xs font-semibold text-slate-600">
          Availability
          <select
            className="mt-1 block rounded-xl border border-stone-300 p-3"
            value={params.get('availability') || ''}
            onChange={(e) => filter('availability', e.target.value)}
          >
            <option value="">All listings</option>
            <option value="true">Available</option>
            <option value="false">Unavailable</option>
          </select>
        </label>
        <button
          onClick={() => setParams({})}
          className="px-3 py-3 text-sm underline"
          type="button"
        >
          Clear filters
        </button>
      </div>
      {loading ? (
        <p role="status">Finding items in your community…</p>
      ) : error ? (
        <div role="alert" className="rounded-2xl bg-red-50 p-6 text-red-800">
          {error}
          <Link to="/app" className="mt-3 block underline">
            Manage your community
          </Link>
        </div>
      ) : (
        <>
          <p className="mb-4 text-sm text-slate-500">
            {result.total} items in your community
          </p>
          {result.items.length ? (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {result.items.map((item) => (
                <ProductCard key={item.id} item={item} />
              ))}
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-stone-300 p-12 text-center">
              <h2 className="text-xl font-bold">No items found</h2>
              <p className="mt-2 text-slate-500">
                Try different filters or be the first to list something.
              </p>
            </div>
          )}
          <div className="mt-8 flex justify-between">
            <button
              disabled={offset === 0}
              onClick={() => {
                const next = new URLSearchParams(params)
                next.set('offset', String(Math.max(0, offset - 24)))
                setParams(next)
              }}
              className="rounded-xl border px-5 py-2 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={offset + 24 >= result.total}
              onClick={() => {
                const next = new URLSearchParams(params)
                next.set('offset', String(offset + 24))
                setParams(next)
              }}
              className="rounded-xl border px-5 py-2 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  )
}
