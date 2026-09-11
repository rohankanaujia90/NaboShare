import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { NaboScoreBadge } from '../components/NaboScoreBadge'
import { getUserProfile, type PublicUser } from '../lib/auth-api'

export function UserProfilePage() {
  const { id } = useParams()
  const { accessToken } = useAuth()
  const [profile, setProfile] = useState<PublicUser | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!accessToken || !id) return
    let active = true
    setProfile(null)
    setError('')
    void getUserProfile(accessToken, id)
      .then((value) => {
        if (active) setProfile(value)
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error ? reason.message : 'Unable to load profile',
          )
      })
    return () => {
      active = false
    }
  }, [accessToken, id])
  return (
    <section className="mx-auto max-w-3xl px-5 py-10">
      <Link to="/rentals" className="text-sm font-bold text-emerald-700">
        ← Back to rentals
      </Link>
      {error && (
        <p role="alert" className="mt-6 rounded-xl bg-red-50 p-4 text-red-800">
          {error}
        </p>
      )}
      {!profile && !error && (
        <p role="status" className="mt-8">
          Loading profile…
        </p>
      )}
      {profile && (
        <div className="mt-8 rounded-3xl border bg-white p-8 shadow-sm">
          <p className="text-sm font-bold uppercase tracking-widest text-emerald-700">
            Community profile
          </p>
          <h1 className="my-5 text-4xl font-black">{profile.full_name}</h1>
          <NaboScoreBadge
            score={profile.nabo_score}
            label={profile.nabo_label}
            prominent
          />
          <p className="mt-6 text-sm text-slate-500">
            NaboScore reflects completed rentals, ratings, cancellations and
            damage reports. Scores range from 0 to 100.
          </p>
        </div>
      )}
    </section>
  )
}
