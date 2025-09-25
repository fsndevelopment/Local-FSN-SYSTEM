"use client"

import { useState, useEffect } from "react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"
import { calculateDeviceFeasibility, getFeasibilityColorClasses, formatExecutionTime, type FeasibilityResult } from "@/lib/utils/feasibility-calculator"

interface FeasibilityIndicatorProps {
  deviceId: string
  accounts: any[]
  template: any
  className?: string
  showDetails?: boolean
}

export function FeasibilityIndicator({ 
  deviceId, 
  accounts, 
  template, 
  className = "",
  showDetails = false 
}: FeasibilityIndicatorProps) {
  const [feasibility, setFeasibility] = useState<FeasibilityResult | null>(null)

  // Calculate feasibility whenever accounts or template change
  useEffect(() => {
    const result = calculateDeviceFeasibility({ accounts, template })
    setFeasibility(result)
  }, [accounts, template, deviceId])

  if (!feasibility) {
    return null
  }

  const colors = getFeasibilityColorClasses(feasibility.status)

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`flex items-center space-x-2 ${className}`}>
            {/* Status Dot */}
            <div className={`w-3 h-3 rounded-full ${colors.dot}`} />
            
            {/* Optional Details */}
            {showDetails && (
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-600">
                  {accounts.length} accounts
                </span>
                <Badge className={`text-xs ${colors.bg} ${colors.text} ${colors.border}`}>
                  {feasibility.utilizationPercentage}%
                </Badge>
              </div>
            )}
          </div>
        </TooltipTrigger>
        
        <TooltipContent className="max-w-sm p-4 bg-white border shadow-lg">
          <div className="space-y-3">
            {/* Status Message */}
            <div className={`p-3 rounded-lg ${colors.bg} ${colors.border} border`}>
              <p className={`text-sm font-semibold ${colors.text}`}>
                {feasibility.message}
              </p>
            </div>

            {/* Breakdown */}
            <div className="space-y-2 text-xs text-gray-600">
              <div className="font-semibold text-gray-900">Execution Breakdown:</div>
              <div className="grid grid-cols-2 gap-2">
                <div>Accounts:</div>
                <div className="font-medium">{feasibility.breakdown.totalAccounts}</div>
                
                <div>Total Sessions:</div>
                <div className="font-medium">{feasibility.breakdown.totalSessions}</div>
                
                <div>Execution Time:</div>
                <div className="font-medium">{formatExecutionTime(feasibility.breakdown.totalExecutionTime)}</div>
                
                <div>Available Time:</div>
                <div className="font-medium">{formatExecutionTime(feasibility.timeAvailable)}</div>
                
                <div>Utilization:</div>
                <div className={`font-medium ${colors.text}`}>
                  {feasibility.utilizationPercentage}%
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {feasibility.recommendations && feasibility.recommendations.length > 0 && (
              <div className="space-y-2">
                <div className="font-semibold text-gray-900 text-xs">Recommendations:</div>
                <ul className="space-y-1">
                  {feasibility.recommendations.map((rec, index) => (
                    <li key={index} className="text-xs text-gray-600 flex items-start space-x-1">
                      <span className="text-gray-400">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// Compact version for smaller spaces
export function CompactFeasibilityIndicator({ deviceId, accounts, template }: FeasibilityIndicatorProps) {
  return (
    <FeasibilityIndicator 
      deviceId={deviceId}
      accounts={accounts}
      template={template}
      className="inline-flex"
      showDetails={false}
    />
  )
}

// Detailed version with full breakdown
export function DetailedFeasibilityIndicator({ deviceId, accounts, template }: FeasibilityIndicatorProps) {
  return (
    <FeasibilityIndicator 
      deviceId={deviceId}
      accounts={accounts}
      template={template}
      className="flex"
      showDetails={true}
    />
  )
}
