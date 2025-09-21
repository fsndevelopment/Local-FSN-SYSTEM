import type React from "react"
import { cn } from "@/lib/utils"

interface RiskBadgeProps {
  risk: "SAFE" | "NORMAL" | "AGGRESSIVE"
  children: React.ReactNode
  className?: string
}

export function RiskBadge({ risk, children, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
        {
          "bg-green-100 text-green-800": risk === "SAFE",
          "bg-yellow-100 text-yellow-800": risk === "NORMAL",
          "bg-red-100 text-red-800": risk === "AGGRESSIVE",
        },
        className,
      )}
    >
      {children}
    </span>
  )
}
