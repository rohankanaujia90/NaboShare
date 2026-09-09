import { Link, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <main className="min-h-screen bg-stone-50 text-slate-950">
      <nav className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6">
        <Link className="text-xl font-black tracking-tight" to="/">
          Nabo<span className="text-emerald-600">Share</span>
        </Link>
        <div className="flex items-center gap-3 text-sm font-semibold">
          {user ? (
            <>
              <Link to="/marketplace" className="text-emerald-800">
                Browse
              </Link>
              <Link to="/rentals" className="text-emerald-800">
                Rentals
              </Link>
              <Link to="/app" className="text-slate-600 sm:hidden">
                Account
              </Link>
              <Link className="hidden text-slate-600 sm:block" to="/app">
                {user.full_name}
              </Link>
              <button
                className="rounded-full border border-slate-300 px-4 py-2 transition hover:border-slate-950"
                onClick={logout}
                type="button"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link className="px-3 py-2" to="/login">
                Log in
              </Link>
              <Link
                className="rounded-full bg-emerald-700 px-4 py-2 text-white transition hover:bg-emerald-800"
                to="/register"
              >
                Join NaboShare
              </Link>
            </>
          )}
        </div>
      </nav>
      <Outlet />
    </main>
  )
}
