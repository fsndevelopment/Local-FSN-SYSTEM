import type React from "react"
import { ChevronLeft, ChevronRight, LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

interface HeroCardProps {
  title: string
  subtitle?: string
  showNavigation?: boolean
  children?: React.ReactNode
  icon?: LucideIcon
}

export function HeroCard({ title, subtitle, showNavigation = false, children, icon: Icon }: HeroCardProps) {
  return (
    <div className="bg-card rounded-2xl shadow p-6 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          {/* Icon */}
          <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center">
            {Icon ? (
              <Icon className="w-8 h-8 text-muted-foreground" />
            ) : (
              <div className="w-8 h-8 bg-foreground rounded-full opacity-20"></div>
            )}
          </div>

          <div>
            <h1 className="text-xl font-semibold text-foreground">{title}</h1>
            {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {children}

          {showNavigation && (
            <>
              <Button variant="outline" size="icon" className="rounded-full w-10 h-10 border-border bg-transparent">
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="icon" className="rounded-full w-10 h-10 border-border bg-transparent">
                <ChevronRight className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
