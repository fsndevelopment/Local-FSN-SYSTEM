/**
 * Tracking Hooks
 * 
 * React Query hooks for follower tracking operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Tracking data types
export interface FollowerTrackingEntry {
  username: string
  name: string
  followers_count: number
  followers_raw: string
  bio: string
  scan_timestamp: string
  device_id: string
  job_id: string
}

export interface UserFollowerHistory {
  username: string
  history: FollowerTrackingEntry[]
  total: number
}

export interface FollowerTrackingResponse {
  tracking_data: FollowerTrackingEntry[]
  total: number
}

// Get all follower tracking data
export function useFollowerTracking() {
  return useQuery({
    queryKey: ['tracking', 'followers'],
    queryFn: async (): Promise<FollowerTrackingResponse> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/tracking/followers`)
      if (!response.ok) {
        throw new Error('Failed to fetch tracking data')
      }
      return response.json()
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  })
}

// Get follower history for specific user
export function useUserFollowerHistory(username: string) {
  return useQuery({
    queryKey: ['tracking', 'followers', username],
    queryFn: async (): Promise<UserFollowerHistory> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/tracking/followers/${username}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch tracking data for ${username}`)
      }
      return response.json()
    },
    enabled: !!username,
    staleTime: 30 * 1000,
  })
}

// Manual profile scan trigger
export function useManualProfileScan() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (deviceId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/v1/tracking/scan/${deviceId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to trigger profile scan')
      }
      
      return response.json()
    },
    onSuccess: (data) => {
      // Invalidate tracking queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['tracking'] })
      
      if (data.success) {
        toast.success('Profile scan completed!', {
          description: `Updated stats for ${data.data?.username || 'account'}`
        })
      } else {
        toast.error('Profile scan failed', {
          description: data.message
        })
      }
    },
    onError: (error: any) => {
      toast.error('Scan failed', {
        description: error.message || 'Unknown error occurred'
      })
    },
  })
}

// Helper function to calculate growth
export function calculateGrowth(history: FollowerTrackingEntry[]): {
  dailyGrowth: number
  weeklyGrowth: number
  totalGrowth: number
} {
  if (history.length < 2) {
    return { dailyGrowth: 0, weeklyGrowth: 0, totalGrowth: 0 }
  }

  const latest = history[history.length - 1]
  const previous = history[history.length - 2]
  const oldest = history[0]

  const dailyGrowth = latest.followers_count - previous.followers_count
  const totalGrowth = latest.followers_count - oldest.followers_count

  // Calculate weekly growth (last 7 entries or available entries)
  const weekStart = Math.max(0, history.length - 7)
  const weeklyStartCount = history[weekStart].followers_count
  const weeklyGrowth = latest.followers_count - weeklyStartCount

  return {
    dailyGrowth,
    weeklyGrowth,
    totalGrowth
  }
}