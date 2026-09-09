import { useState } from 'react'
import { Link } from 'react-router-dom'
import { type Item, money } from '../lib/items-api'

export function ItemImage({
  item,
}: {
  item: Pick<Item, 'title' | 'image_url' | 'category'>
}) {
  const [failed, setFailed] = useState(false)
  return item.image_url && !failed ? (
    <img
      className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
      src={item.image_url}
      alt={item.title}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  ) : (
    <div className="grid h-full place-items-center bg-emerald-50 text-lg font-semibold text-emerald-800">
      {item.category}
    </div>
  )
}

export function ProductCard({ item }: { item: Item }) {
  return (
    <Link
      to={`/items/${item.id}`}
      className="group overflow-hidden rounded-3xl border border-stone-200 bg-white transition hover:-translate-y-1 hover:shadow-lg focus-visible:outline-emerald-600"
    >
      <div className="relative aspect-[4/3] overflow-hidden">
        <ItemImage item={item} />
        <span className="absolute left-3 top-3 rounded-full bg-white/95 px-3 py-1 text-xs font-bold">
          {item.availability ? 'Available' : 'Unavailable'}
        </span>
      </div>
      <div className="p-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
          {item.category}
        </p>
        <h2 className="mt-2 truncate text-xl font-bold">{item.title}</h2>
        <p className="mt-4 text-xl font-black">
          {money(item.rental_price_per_day)}
          <span className="text-sm font-normal text-slate-500"> / day</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">
          {money(item.security_deposit)} security deposit
        </p>
      </div>
    </Link>
  )
}
