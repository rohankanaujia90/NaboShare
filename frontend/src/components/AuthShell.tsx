import type { PropsWithChildren, ReactNode } from 'react'
import { Link } from 'react-router-dom'

type AuthShellProps = PropsWithChildren<{
  title: string
  subtitle: string
  footer: ReactNode
}>

export function AuthShell({
  title,
  subtitle,
  footer,
  children,
}: AuthShellProps) {
  return (
    <section className="mx-auto grid max-w-6xl gap-12 px-6 py-12 lg:grid-cols-2 lg:py-20">
      <div className="hidden rounded-3xl bg-emerald-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link className="text-2xl font-black" to="/">
          Nabo<span className="text-emerald-300">Share</span>
        </Link>
        <blockquote className="text-3xl font-bold leading-tight">
          Good things deserve to be used, not left gathering dust.
        </blockquote>
        <p className="text-sm text-emerald-100/70">
          Share locally. Borrow confidently.
        </p>
      </div>

      <div className="mx-auto w-full max-w-md py-6">
        <h1 className="text-4xl font-black tracking-tight">{title}</h1>
        <p className="mt-3 text-slate-600">{subtitle}</p>
        <div className="mt-8">{children}</div>
        <div className="mt-6 text-center text-sm text-slate-600">{footer}</div>
      </div>
    </section>
  )
}
