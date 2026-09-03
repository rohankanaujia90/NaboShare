const categories = ['Tools', 'Electronics', 'Travel', 'Outdoors']

export function App() {
  return (
    <main className="min-h-screen bg-stone-50 text-slate-950">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <a className="text-xl font-black tracking-tight" href="/">
          Nabo<span className="text-emerald-600">Share</span>
        </a>
        <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
          MVP foundation
        </span>
      </nav>

      <section className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div>
          <p className="mb-4 text-sm font-bold uppercase tracking-[0.2em] text-emerald-700">
            Your community, better shared
          </p>
          <h1 className="max-w-3xl text-5xl font-black leading-[1.05] tracking-tight sm:text-7xl">
            Borrow what you need. Share what you have.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            A trusted rental marketplace for verified colleges, hostels, and
            residential societies.
          </p>
        </div>

        <div className="rounded-3xl bg-emerald-950 p-8 text-white shadow-2xl shadow-emerald-950/20">
          <p className="text-sm font-semibold text-emerald-300">
            Explore nearby
          </p>
          <div className="mt-6 grid grid-cols-2 gap-3">
            {categories.map((category) => (
              <div
                className="rounded-2xl border border-white/10 bg-white/10 px-4 py-6 font-semibold"
                key={category}
              >
                {category}
              </div>
            ))}
          </div>
          <p className="mt-6 text-sm leading-6 text-emerald-100/80">
            Listings, verification, and rentals are coming next.
          </p>
        </div>
      </section>
    </main>
  )
}
