// Feasibility Calculator for Device Workload Assessment

export interface FeasibilityResult {
  status: 'green' | 'orange' | 'red' | 'neutral'
  message: string
  timeUsed: number // minutes
  timeAvailable: number // minutes
  utilizationPercentage: number
  recommendations?: string[]
  breakdown: {
    totalAccounts: number
    totalSessions: number
    firstRoundTime: number
    otherRoundsTime: number
    totalExecutionTime: number
  }
}

export interface DeviceFeasibilityInput {
  accounts: any[] // Accounts assigned to device
  template: {
    textPostsPerDay?: number
    photosPostsPerDay?: number
    scrollingTimeMinutes?: number
    intervalBetweenPosts?: number // hours
  } | null
}

export function calculateDeviceFeasibility(input: DeviceFeasibilityInput): FeasibilityResult {
  const { accounts, template } = input

  // Default neutral state
  if (!template || accounts.length === 0) {
    return {
      status: 'neutral',
      message: 'No template or accounts assigned',
      timeUsed: 0,
      timeAvailable: 900, // 15 hours
      utilizationPercentage: 0,
      breakdown: {
        totalAccounts: 0,
        totalSessions: 0,
        firstRoundTime: 0,
        otherRoundsTime: 0,
        totalExecutionTime: 0
      }
    }
  }

  // Extract template settings
  const textPosts = template.textPostsPerDay || 0
  const photoPosts = template.photosPostsPerDay || 0
  const totalPostsPerAccount = textPosts + photoPosts
  const scrollingTime = template.scrollingTimeMinutes || 10
  const intervalHours = template.intervalBetweenPosts || 1

  // Calculate timing
  const totalAccounts = accounts.length
  const totalSessions = totalAccounts * totalPostsPerAccount

  // Time breakdown
  const sessionDuration = 5 // minutes per post
  const overhead = 2 // app close + profile extraction
  const baseSessionTime = sessionDuration + overhead // 7 minutes

  // First round (with scrolling)
  const firstSessionTime = baseSessionTime + scrollingTime
  const firstRoundTime = totalAccounts * firstSessionTime

  // Other rounds (post only)
  const otherRoundsCount = totalPostsPerAccount - 1
  const otherRoundsTime = totalAccounts * otherRoundsCount * baseSessionTime

  // Total execution time
  const totalExecutionTime = firstRoundTime + otherRoundsTime

  // Available time (15 hours = 900 minutes)
  const availableTime = 15 * 60

  // Calculate utilization
  const utilizationPercentage = Math.round((totalExecutionTime / availableTime) * 100)

  // Determine status and recommendations
  let status: 'green' | 'orange' | 'red'
  let message: string
  let recommendations: string[] = []

  if (utilizationPercentage <= 70) {
    status = 'green'
    message = `✅ Perfect fit - ${totalAccounts} accounts, ${totalPostsPerAccount} posts each`
    recommendations = [
      'Excellent configuration!',
      'You can add more accounts if needed',
      `Estimated completion: ${Math.round(totalExecutionTime / 60)} hours`
    ]
  } else if (utilizationPercentage <= 100) {
    status = 'orange'
    message = `⚠️ Tight schedule - may not complete all ${totalPostsPerAccount} posts`
    recommendations = [
      `Consider reducing posts to ${Math.floor((availableTime * 0.7) / (totalAccounts * baseSessionTime))} per account`,
      'Or reduce scrolling time to under 10 minutes',
      `Current utilization: ${utilizationPercentage}%`
    ]
  } else {
    status = 'red'
    const maxAccountsForCurrentSettings = Math.floor(availableTime * 0.8 / (firstSessionTime + (otherRoundsCount * baseSessionTime)))
    const maxPostsForCurrentAccounts = Math.floor((availableTime * 0.8) / (totalAccounts * baseSessionTime))
    
    message = `❌ Won't fit - reduce accounts or posts`
    recommendations = [
      `Maximum accounts for ${totalPostsPerAccount} posts: ${maxAccountsForCurrentSettings}`,
      `Or maximum posts for ${totalAccounts} accounts: ${maxPostsForCurrentAccounts}`,
      'Consider using multiple devices',
      `Current utilization: ${utilizationPercentage}%`
    ]
  }

  return {
    status,
    message,
    timeUsed: totalExecutionTime,
    timeAvailable: availableTime,
    utilizationPercentage,
    recommendations,
    breakdown: {
      totalAccounts,
      totalSessions,
      firstRoundTime,
      otherRoundsTime,
      totalExecutionTime
    }
  }
}

// Helper function to format time for display
export function formatExecutionTime(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  
  if (hours === 0) {
    return `${mins} minutes`
  } else if (mins === 0) {
    return `${hours} hours`
  } else {
    return `${hours}h ${mins}m`
  }
}

// Helper function to get status color classes
export function getFeasibilityColorClasses(status: string) {
  switch (status) {
    case 'green':
      return {
        dot: 'bg-green-500',
        text: 'text-green-700',
        bg: 'bg-green-50',
        border: 'border-green-200'
      }
    case 'orange':
      return {
        dot: 'bg-orange-500',
        text: 'text-orange-700', 
        bg: 'bg-orange-50',
        border: 'border-orange-200'
      }
    case 'red':
      return {
        dot: 'bg-red-500 animate-pulse',
        text: 'text-red-700',
        bg: 'bg-red-50', 
        border: 'border-red-200'
      }
    default:
      return {
        dot: 'bg-gray-400',
        text: 'text-gray-600',
        bg: 'bg-gray-50',
        border: 'border-gray-200'
      }
  }
}
