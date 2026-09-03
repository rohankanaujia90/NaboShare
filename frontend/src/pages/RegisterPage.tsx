import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { AuthShell } from '../components/AuthShell'
import { FormField } from '../components/FormField'
import { ApiError } from '../lib/api'

export function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (user) return <Navigate replace to="/app" />

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
      setError('Password must contain at least one letter and one number.')
      return
    }

    setIsSubmitting(true)
    try {
      await register({
        full_name: form.fullName,
        email: form.email,
        phone: form.phone || null,
        password: form.password,
      })
      void navigate('/app', { replace: true })
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : 'Unable to create your account. Please try again.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthShell
      footer={
        <>
          Already have an account?{' '}
          <Link className="font-bold text-emerald-700" to="/login">
            Log in
          </Link>
        </>
      }
      subtitle="Join people sharing useful things in their communities."
      title="Create your account"
    >
      <form
        className="space-y-5"
        onSubmit={(event) => void handleSubmit(event)}
      >
        <FormField
          autoComplete="name"
          id="full-name"
          label="Full name"
          minLength={2}
          onChange={(event) => updateField('fullName', event.target.value)}
          required
          value={form.fullName}
        />
        <FormField
          autoComplete="email"
          id="register-email"
          label="Email"
          onChange={(event) => updateField('email', event.target.value)}
          placeholder="you@example.com"
          required
          type="email"
          value={form.email}
        />
        <FormField
          autoComplete="tel"
          id="phone"
          label="Phone (optional)"
          onChange={(event) => updateField('phone', event.target.value)}
          type="tel"
          value={form.phone}
        />
        <FormField
          autoComplete="new-password"
          id="register-password"
          label="Password"
          minLength={8}
          onChange={(event) => updateField('password', event.target.value)}
          required
          type="password"
          value={form.password}
        />
        <p className="-mt-3 text-xs text-slate-500">
          At least 8 characters with one letter and one number.
        </p>
        <FormField
          autoComplete="new-password"
          id="confirm-password"
          label="Confirm password"
          minLength={8}
          onChange={(event) =>
            updateField('confirmPassword', event.target.value)
          }
          required
          type="password"
          value={form.confirmPassword}
        />
        {error && (
          <p
            className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
            role="alert"
          >
            {error}
          </p>
        )}
        <button
          className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-bold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthShell>
  )
}
