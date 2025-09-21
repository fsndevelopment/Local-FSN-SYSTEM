/**
 * Real-time Updates Hook
 * 
 * Provides real-time data synchronization using React Query
 */

import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'

interface UseRealtimeOptions {
  interval?: number // Polling interval in milliseconds
  enabled?: boolean // Whether real-time updates are enabled
  queryKeys?: string[][] // Specific query keys to refetch
}

/**
 * Hook for real-time data updates
 * 
 * This hook provides automatic data refreshing for live updates.
 * In a full implementation, this would use WebSockets, but for now
 * it uses intelligent polling with React Query.
 */
export function useRealtime(options: UseRealtimeOptions = {}) {
  const {
    interval = 30000, // 30 seconds default
    enabled = false,
    queryKeys = []
  } = options

  const queryClient = useQueryClient()
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // Set up polling interval
    intervalRef.current = setInterval(async () => {
      console.log('🔄 Real-time update: Refreshing data...')
      
      try {
        if (queryKeys.length > 0) {
          // Refetch specific queries
          for (const queryKey of queryKeys) {
            await queryClient.refetchQueries({ queryKey })
          }
        } else {
          // Refetch all active queries
          await queryClient.refetchQueries({ type: 'active' })
        }
      } catch (error) {
        console.error('Real-time update failed:', error)
      }
    }, interval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, interval, queryKeys, queryClient])

  // Manual refresh function
  const refresh = async () => {
    console.log('🔄 Manual refresh triggered')
    
    try {
      if (queryKeys.length > 0) {
        for (const queryKey of queryKeys) {
          await queryClient.refetchQueries({ queryKey })
        }
      } else {
        await queryClient.refetchQueries({ type: 'active' })
      }
    } catch (error) {
      console.error('Manual refresh failed:', error)
    }
  }

  return {
    refresh,
    isEnabled: enabled,
  }
}

/**
 * Hook for dashboard real-time updates
 * 
 * Specialized hook for dashboard data that needs frequent updates
 */
export function useDashboardRealtime(enabled: boolean = false) {
  return useRealtime({
    interval: 15000, // 15 seconds for dashboard
    enabled,
    queryKeys: [
      ['devices'],
      ['jobs'],
      ['device-stats'],
    ]
  })
}

/**
 * Hook for job queue real-time updates
 * 
 * Specialized hook for job queue monitoring
 */
export function useJobQueueRealtime(enabled: boolean = false) {
  return useRealtime({
    interval: 5000, // 5 seconds for active job monitoring
    enabled,
    queryKeys: [
      ['jobs'],
    ]
  })
}

/**
 * Hook for tracking real-time updates
 * 
 * Specialized hook for analytics and tracking data
 */
export function useTrackingRealtime(enabled: boolean = false) {
  return useRealtime({
    interval: 60000, // 1 minute for analytics
    enabled,
    queryKeys: [
      ['tracking-summary'],
      ['tracking-accounts'],
    ]
  })
}
