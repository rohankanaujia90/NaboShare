import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { FormField } from '../components/FormField'
import {
  categories,
  itemRequest,
  type Item,
  type ItemInput,
  type Category,
} from '../lib/items-api'

const empty: ItemInput = {
  title: '',
  description: '',
  category: 'Other',
  rental_price_per_day: '',
  security_deposit: '',
  replacement_value: '',
  image_url: null,
  availability: true,
}

export function ItemFormPage() {
  const { id } = useParams()
  const { accessToken, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<ItemInput>(empty)
  const [loading, setLoading] = useState(Boolean(id))
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [allowed, setAllowed] = useState(!id)
  useEffect(() => {
    if (!id || !accessToken) return
    let active = true
    void itemRequest<Item>(accessToken, `/${id}`)
      .then((item) => {
        if (!active) return
        if (item.owner_id !== user?.id) {
          setError('Only the owner can edit this item')
          return
        }
        const {
          title,
          description,
          category,
          rental_price_per_day,
          security_deposit,
          replacement_value,
          image_url,
          availability,
        } = item
        setForm({
          title,
          description,
          category,
          rental_price_per_day,
          security_deposit,
          replacement_value,
          image_url,
          availability,
        })
        setAllowed(true)
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
  }, [id, accessToken, user?.id])
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!accessToken) return
    setSaving(true)
    setError('')
    try {
      const item = await itemRequest<Item>(
        accessToken,
        id ? `/${id}` : '',
        id ? 'PATCH' : 'POST',
        form,
      )
      void navigate(`/items/${item.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save item')
    } finally {
      setSaving(false)
    }
  }
  return (
    <section className="mx-auto max-w-2xl px-5 py-8">
      <Link className="text-sm text-emerald-700" to="/marketplace">
        ← Marketplace
      </Link>
      <h1 className="mt-6 text-4xl font-black">
        {id ? 'Edit your listing' : 'Give your things a second outing.'}
      </h1>
      <p className="mb-8 mt-3 text-slate-500">
        Your listing will only be visible to your community.
      </p>
      {error && (
        <p role="alert" className="mb-5 rounded-xl bg-red-50 p-4 text-red-800">
          {error}{' '}
          <Link to="/app" className="underline">
            Community settings
          </Link>
        </p>
      )}
      {loading ? (
        <p role="status">Loading item…</p>
      ) : (
        allowed && (
          <form
            onSubmit={(e) => void submit(e)}
            className="space-y-5 rounded-3xl border border-stone-200 bg-white p-5 sm:p-8"
          >
            <FormField
              id="title"
              label="Item title"
              required
              minLength={2}
              maxLength={160}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <label className="block text-sm font-bold">
              Description
              <textarea
                className="mt-2 block min-h-32 w-full rounded-xl border border-stone-300 p-3 font-normal"
                required
                minLength={10}
                maxLength={5000}
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                placeholder="Condition, included accessories, and anything a borrower should know"
              />
            </label>
            <label className="block text-sm font-bold">
              Category
              <select
                className="mt-2 block w-full rounded-xl border border-stone-300 p-3"
                value={form.category}
                onChange={(e) =>
                  setForm({ ...form, category: e.target.value as Category })
                }
              >
                {categories.map((category) => (
                  <option key={category}>{category}</option>
                ))}
              </select>
            </label>
            <div className="grid gap-4 sm:grid-cols-3">
              {(
                [
                  'rental_price_per_day',
                  'security_deposit',
                  'replacement_value',
                ] as const
              ).map((key, index) => (
                <FormField
                  key={key}
                  id={key}
                  label={
                    ['Price / day (₹)', 'Deposit (₹)', 'Replacement value (₹)'][
                      index
                    ]
                  }
                  type="number"
                  required
                  min="0"
                  max="9999999999.99"
                  step="0.01"
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              ))}
            </div>
            <FormField
              id="image"
              label="Image URL (optional)"
              type="url"
              maxLength={2048}
              placeholder="https://…"
              value={form.image_url || ''}
              onChange={(e) =>
                setForm({ ...form, image_url: e.target.value || null })
              }
            />
            <label className="flex items-center gap-3 text-sm">
              <input
                type="checkbox"
                checked={form.availability}
                onChange={(e) =>
                  setForm({ ...form, availability: e.target.checked })
                }
              />
              Available to rent
            </label>
            <button
              disabled={saving}
              className="w-full rounded-xl bg-emerald-800 px-5 py-4 font-bold text-white disabled:opacity-50"
            >
              {saving ? 'Saving…' : id ? 'Save changes' : 'Publish item'}
            </button>
          </form>
        )
      )}
    </section>
  )
}
