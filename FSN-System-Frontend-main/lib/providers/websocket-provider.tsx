/**
 * WebSocket Provider
 * 
 * Provides WebSocket context to the entire application for real-time updates.
 * Automatically manages connection and broadcasts updates to all components.
 */

'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useWebSocket, WebSocketState, WebSocketMessage } from '@/lib/hooks/use-websocket'
import { toast } from 'sonner'

interface WebSocketContextType {
  state: WebSocketState
  lastMessage: WebSocketMessage | null
  connectionStats: { active_connections: number }
  isConnected: boolean
  isConnecting: boolean
  isDisconnected: boolean
  hasError: boolean
  connect: () => void
  disconnect: () => void
  ping: () => void
  subscribe: (type: 'devices' | 'jobs' | 'system' | 'all') => void
  getStatus: () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

interface WebSocketProviderProps {
  children: React.ReactNode
  autoConnect?: boolean
}

export function WebSocketProvider({ children, autoConnect = true }: WebSocketProviderProps) {
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  const [lastConnectionTime, setLastConnectionTime] = useState<Date | null>(null)

  const websocket = useWebSocket({
    autoConnect,
    onConnect: () => {
      setConnectionAttempts(0)
      setLastConnectionTime(new Date())
      console.log('🔌 WebSocket connected')
    },
    onDisconnect: () => {
      console.log('🔌 WebSocket disconnected')
    },
    onError: (error) => {
      console.error('🔌 WebSocket error:', error)
      setConnectionAttempts(prev => prev + 1)
    }
  })

  // Show connection status notifications
  useEffect(() => {
    if (websocket.isConnected && lastConnectionTime) {
      const timeSinceLastConnection = Date.now() - lastConnectionTime.getTime()
      if (timeSinceLastConnection > 1000) { // Only show if not initial connection
        toast.success('Real-time updates connected', {
          description: 'Live device status and job progress monitoring active'
        })
      }
    }
  }, [websocket.isConnected, lastConnectionTime])

  useEffect(() => {
    if (websocket.hasError && connectionAttempts > 0) {
      toast.error('Real-time updates disconnected', {
        description: `Attempting to reconnect... (${connectionAttempts}/10)`
      })
    }
  }, [websocket.hasError, connectionAttempts])

  // Auto-reconnect notification
  useEffect(() => {
    if (websocket.isDisconnected && connectionAttempts > 0 && connectionAttempts < 10) {
      const timer = setTimeout(() => {
        toast.info('Reconnecting to real-time updates...', {
          description: 'Attempting to restore live monitoring'
        })
      }, 2000)

      return () => clearTimeout(timer)
    }
  }, [websocket.isDisconnected, connectionAttempts])

  const contextValue: WebSocketContextType = {
    ...websocket,
    // Add any additional context-specific methods here
  }

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}

// Hook for components that need WebSocket connection status
export function useConnectionStatus() {
  const { state, isConnected, isConnecting, isDisconnected, hasError, connectionStats } = useWebSocketContext()
  
  return {
    state,
    isConnected,
    isConnecting,
    isDisconnected,
    hasError,
    activeConnections: connectionStats.active_connections,
    statusText: getStatusText(state),
    statusColor: getStatusColor(state)
  }
}

function getStatusText(state: WebSocketState): string {
  switch (state) {
    case 'connecting':
      return 'Connecting...'
    case 'connected':
      return 'Connected'
    case 'disconnected':
      return 'Disconnected'
    case 'error':
      return 'Error'
    default:
      return 'Unknown'
  }
}

function getStatusColor(state: WebSocketState): string {
  switch (state) {
    case 'connecting':
      return 'text-yellow-500'
    case 'connected':
      return 'text-green-500'
    case 'disconnected':
      return 'text-gray-500'
    case 'error':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}
