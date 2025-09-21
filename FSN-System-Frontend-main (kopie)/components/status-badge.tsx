import type React from "react"
import { cn } from "@/lib/utils"

interface StatusBadgeProps {
  status: "active" | "inactive" | "error" | "pending" | "success"
  children: React.ReactNode
  className?: string
}

export function StatusBadge({ status, children, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
        {
          "bg-green-100 text-green-800": status === "active" || status === "success",
          "bg-gray-100 text-gray-800": status === "inactive",
          "bg-red-100 text-red-800": status === "error",
          "bg-yellow-100 text-yellow-800": status === "pending",
        },
        className,
      )}
    >
      {children}
    </span>
  )
}
