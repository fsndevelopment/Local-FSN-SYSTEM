interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  className?: string
}

export function StatCard({ title, value, subtitle, className }: StatCardProps) {
  return (
    <div className={`bg-card rounded-2xl shadow p-6 ${className || ""}`}>
      <div className="text-2xl font-bold text-foreground mb-1">{value}</div>
      <div className="text-sm font-medium text-foreground mb-1">{title}</div>
      {subtitle && <div className="text-xs text-muted-foreground">{subtitle}</div>}
    </div>
  )
}
