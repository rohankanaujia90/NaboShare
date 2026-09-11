import { Link } from 'react-router-dom'

const styles: Record<string, string> = {
  Excellent: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  Good: 'bg-sky-100 text-sky-800 ring-sky-200',
  Average: 'bg-amber-100 text-amber-900 ring-amber-200',
  Risky: 'bg-red-100 text-red-800 ring-red-200',
}

type Props = {
  id?: string
  name?: string
  score: number
  label: string
  prominent?: boolean
}

export function NaboScoreBadge({ id, name, score, label, prominent }: Props) {
  const content = (
    <span
      className={`inline-flex items-center gap-2 rounded-2xl px-3 py-2 font-bold ring-1 ${styles[label] ?? styles.Risky} ${prominent ? 'text-lg' : 'text-sm'}`}
    >
      {name && <span>{name}</span>}
      <span className={prominent ? 'text-3xl' : ''}>{score}</span>
      <span className="font-semibold">{label}</span>
    </span>
  )
  return id ? <Link to={`/profiles/${id}`}>{content}</Link> : content
}
