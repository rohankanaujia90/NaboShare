import { useAuth } from '../auth/useAuth'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <p className="text-sm font-bold uppercase tracking-[0.2em] text-emerald-700">
        Your NaboShare
      </p>
      <h1 className="mt-3 text-4xl font-black tracking-tight">
        Welcome, {user?.full_name}
      </h1>
      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        <div className="rounded-3xl border border-slate-200 bg-white p-7">
          <p className="text-sm font-semibold text-slate-500">Nabo score</p>
          <p className="mt-2 text-5xl font-black text-emerald-700">
            {user?.nabo_score}
          </p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-7">
          <p className="text-sm font-semibold text-slate-500">Account email</p>
          <p className="mt-2 font-bold">{user?.email}</p>
        </div>
      </div>
    </section>
  )
}
