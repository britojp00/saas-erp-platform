interface StatCardProps {
  label: string
  value: string
  hint?: string
}

export default function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <article className="stat-card">
      <p className="stat-card__label">{label}</p>
      <p className="stat-card__value">{value}</p>
      {hint !== undefined && <p className="stat-card__hint">{hint}</p>}
    </article>
  )
}
