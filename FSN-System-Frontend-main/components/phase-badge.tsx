import { formatPhase } from "@/lib/utils/time"

interface PhaseBadgeProps {
  account: {
    warmupDay?: number
    posting_start_at?: string | null
  }
}

export function PhaseBadge({ account }: PhaseBadgeProps) {
  const phase = formatPhase(account)

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
      {phase}
    </span>
  )
}
