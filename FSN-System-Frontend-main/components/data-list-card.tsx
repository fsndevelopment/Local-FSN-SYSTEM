"use client"

import type React from "react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

interface DataListItem {
  id: string
  icon?: React.ReactNode
  title: string
  subtitle: string
  meta?: string
  badge?: React.ReactNode
  action?: {
    label: string
    onClick?: () => void
  }
  actions?: Array<{
    label: string
    onClick?: () => void
    variant?: "default" | "outline" | "destructive" | "secondary" | "ghost" | "link"
    icon?: React.ReactNode
  }>
  additionalContent?: React.ReactNode
}

interface DataListCardProps {
  title: string
  items: DataListItem[]
  filters?: React.ReactNode
  isLoading?: boolean
}

export function DataListCard({ title, items, filters, isLoading = false }: DataListCardProps) {
  return (
    <div className="bg-card rounded-2xl shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        {filters}
      </div>

      <div className="space-y-3">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 3 }).map((_, index) => (
            <div
              key={`skeleton-${index}`}
              className="flex items-center justify-between p-3 bg-muted/30 rounded-xl"
            >
              <div className="flex items-center space-x-3">
                <Skeleton className="w-8 h-8 rounded-full" />
                <div>
                  <Skeleton className="h-4 w-32 mb-2" />
                  <Skeleton className="h-3 w-24 mb-1" />
                  <Skeleton className="h-3 w-48" />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Skeleton className="h-6 w-16 rounded-full" />
                <Skeleton className="h-8 w-16 rounded-full" />
              </div>
            </div>
          ))
        ) : items.length === 0 ? (
          // Empty state
          <div className="text-center py-8 text-muted-foreground">
            <div className="text-sm">No items found</div>
          </div>
        ) : (
          // Actual items
          items.map((item) => (
            <div
              key={item.id}
              className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-semibold text-base">{item.title}</div>
                  <div className="text-sm text-muted-foreground mt-1">{item.subtitle}</div>
                  {item.meta && <div className="text-sm text-muted-foreground mt-1">{item.meta}</div>}
                </div>

                <div className="flex items-center space-x-2">
                  {item.badge}
                  {item.actions ? (
                    <div className="flex items-center space-x-1">
                      {item.actions.map((action, index) => (
                        <Button
                          key={index}
                          variant={action.variant || "outline"}
                          size="sm"
                          className={`h-8 ${
                            action.variant === "default" 
                              ? "bg-gray-800 text-white hover:bg-gray-900 border-gray-800" 
                              : action.variant === "destructive"
                              ? "bg-red-500 text-white hover:bg-red-600 border-red-500"
                              : "border-gray-300"
                          }`}
                          onClick={action.onClick}
                        >
                          {action.icon && <span className={action.label ? "mr-1" : ""}>{action.icon}</span>}
                          {action.label && action.label}
                        </Button>
                      ))}
                    </div>
                  ) : item.action && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 bg-gray-800 text-white hover:bg-gray-900 border-gray-800"
                      onClick={item.action.onClick}
                    >
                      {item.action.label}
                    </Button>
                  )}
                </div>
              </div>
              
              {/* Additional Content */}
              {item.additionalContent && item.additionalContent}
            </div>
          ))
        )}
      </div>
    </div>
  )
}