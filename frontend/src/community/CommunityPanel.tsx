import { useState, type FormEvent } from 'react'

import { FormField } from '../components/FormField'
import type { CommunityType } from '../lib/community-api'
import { useCommunity } from './useCommunity'

const typeLabels: Record<CommunityType, string> = {
  college: 'College',
  hostel: 'Hostel',
  apartment_society: 'Apartment society',
  corporate_campus: 'Corporate campus',
}

export function CommunityPanel() {
  const { community, isLoading, error, create, join } = useCommunity()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [inviteCode, setInviteCode] = useState('')
  const [newCommunity, setNewCommunity] = useState<{
    name: string
    city: string
    type: CommunityType
  }>({ name: '', city: '', type: 'college' })

  if (isLoading) {
    return (
      <p className="mt-10 text-sm font-semibold text-slate-500">
        Loading community…
      </p>
    )
  }

  if (community) {
    return (
      <section className="mt-10 rounded-3xl bg-emerald-950 p-8 text-white">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">
          Your verified community
        </p>
        <div className="mt-4 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <h2 className="text-3xl font-black">{community.name}</h2>
            <p className="mt-2 text-emerald-100/75">
              {typeLabels[community.type]} · {community.city}
            </p>
          </div>
          <div className="rounded-2xl bg-white/10 px-5 py-3">
            <p className="text-xs text-emerald-200">Invite code</p>
            <p className="mt-1 font-mono text-xl font-bold tracking-[0.16em]">
              {community.invite_code}
            </p>
          </div>
        </div>
      </section>
    )
  }

  async function handleJoin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    try {
      await join(inviteCode)
    } catch {
      // The hook exposes a user-safe error message.
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    try {
      await create(newCommunity)
    } catch {
      // The hook exposes a user-safe error message.
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="mt-10">
      <p className="text-sm font-bold uppercase tracking-[0.2em] text-emerald-700">
        Get verified
      </p>
      <h2 className="mt-2 text-3xl font-black">Join your local community</h2>
      <p className="mt-2 text-slate-600">
        Enter an invite code, or create a community if you are setting one up.
      </p>

      {error && (
        <p
          className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
          role="alert"
        >
          {error}
        </p>
      )}

      <div className="mt-7 grid gap-6 lg:grid-cols-2">
        <form
          className="rounded-3xl border border-slate-200 bg-white p-7"
          onSubmit={(event) => void handleJoin(event)}
        >
          <h3 className="text-xl font-black">Join with invite code</h3>
          <div className="mt-5">
            <FormField
              autoComplete="off"
              id="invite-code"
              label="Invite code"
              maxLength={12}
              minLength={8}
              onChange={(event) =>
                setInviteCode(event.target.value.toUpperCase())
              }
              placeholder="ABCD2345"
              required
              value={inviteCode}
            />
          </div>
          <button
            className="mt-5 w-full rounded-xl bg-emerald-700 px-4 py-3 font-bold text-white disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            Join community
          </button>
        </form>

        <form
          className="rounded-3xl border border-slate-200 bg-white p-7"
          onSubmit={(event) => void handleCreate(event)}
        >
          <h3 className="text-xl font-black">Create a community</h3>
          <div className="mt-5 space-y-4">
            <FormField
              id="community-name"
              label="Community name"
              minLength={2}
              onChange={(event) =>
                setNewCommunity((value) => ({
                  ...value,
                  name: event.target.value,
                }))
              }
              required
              value={newCommunity.name}
            />
            <FormField
              id="community-city"
              label="City"
              minLength={2}
              onChange={(event) =>
                setNewCommunity((value) => ({
                  ...value,
                  city: event.target.value,
                }))
              }
              required
              value={newCommunity.city}
            />
            <label className="block" htmlFor="community-type">
              <span className="mb-2 block text-sm font-bold text-slate-700">
                Type
              </span>
              <select
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100"
                id="community-type"
                onChange={(event) =>
                  setNewCommunity((value) => ({
                    ...value,
                    type: event.target.value as CommunityType,
                  }))
                }
                value={newCommunity.type}
              >
                {Object.entries(typeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button
            className="mt-5 w-full rounded-xl border border-emerald-700 px-4 py-3 font-bold text-emerald-800 disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            Create community
          </button>
        </form>
      </div>
    </section>
  )
}
