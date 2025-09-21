/**
 * Device Capacity Calculator
 * 
 * Calculates device capacity status based on template and assigned accounts
 */

import { DeviceWithTemplate, Template } from "@/lib/types"

export interface CapacityResult {
  status: "safe" | "warning" | "overloaded"
  reason?: string
  utilization: number // 0-1 percentage
}

/**
 * Calculate device capacity based on template and assigned accounts
 */
export function calculateDeviceCapacity(
  device: DeviceWithTemplate,
  assignedAccounts: any[] = []
): CapacityResult {
  // If no template assigned, device is safe
  if (!device.template) {
    return {
      status: "safe",
      reason: "No template assigned",
      utilization: 0
    }
  }

  const template = device.template
  const accountCount = assignedAccounts.length

  // Calculate daily actions based on template
  const dailyActions = 
    (template.postsPerDay || 0) +
    (template.likesPerDay || 0) +
    (template.followsPerDay || 0) +
    (template.storiesPerDay || 0) +
    (template.commentsPerDay || 0)

  // Calculate total daily actions for all accounts
  const totalDailyActions = dailyActions * accountCount

  // Define capacity thresholds
  const SAFE_THRESHOLD = 100 // Safe up to 100 actions per day
  const WARNING_THRESHOLD = 200 // Warning between 100-200 actions per day
  const OVERLOADED_THRESHOLD = 300 // Overloaded above 200 actions per day

  // Calculate utilization percentage
  const utilization = Math.min(totalDailyActions / OVERLOADED_THRESHOLD, 1)

  // Determine status based on total actions
  if (totalDailyActions <= SAFE_THRESHOLD) {
    return {
      status: "safe",
      reason: `Safe capacity: ${totalDailyActions} actions/day`,
      utilization
    }
  } else if (totalDailyActions <= WARNING_THRESHOLD) {
    return {
      status: "warning",
      reason: `Approaching limit: ${totalDailyActions} actions/day`,
      utilization
    }
  } else {
    return {
      status: "overloaded",
      reason: `Overloaded: ${totalDailyActions} actions/day exceeds safe limits`,
      utilization
    }
  }
}

/**
 * Calculate capacity for multiple devices
 */
export function calculateDevicesCapacity(devices: DeviceWithTemplate[]): Record<string, CapacityResult> {
  const results: Record<string, CapacityResult> = {}
  
  devices.forEach(device => {
    // Mock assigned accounts - in real app, this would come from API
    const assignedAccounts = [] // This would be fetched from API
    results[device.id.toString()] = calculateDeviceCapacity(device, assignedAccounts)
  })
  
  return results
}

/**
 * Get capacity status color class
 */
export function getCapacityStatusColor(status: "safe" | "warning" | "overloaded"): string {
  switch (status) {
    case "safe":
      return "bg-green-100 text-green-800 border-green-200"
    case "warning":
      return "bg-yellow-100 text-yellow-800 border-yellow-200"
    case "overloaded":
      return "bg-red-100 text-red-800 border-red-200"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

/**
 * Get capacity status icon
 */
export function getCapacityStatusIcon(status: "safe" | "warning" | "overloaded"): string {
  switch (status) {
    case "safe":
      return "✅"
    case "warning":
      return "⚠️"
    case "overloaded":
      return "🚨"
    default:
      return "❓"
  }
}
