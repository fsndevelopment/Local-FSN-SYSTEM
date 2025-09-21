/**
 * WebSocket Hook for Real-Time Updates
 * 
 * Provides real-time device status, job progress, and system notifications
 * through WebSocket connection to the backend.
 */

'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

// WebSocket message types
export interface WebSocketMessage {
  type: string
  timestamp: string
  server_time?: number
  [key: string]: any
}

export interface DeviceStatusUpdate extends WebSocketMessage {
  type: 'device_status_update'
  device_id: number
  status: 'active' | 'offline' | 'error'
  details: {
    old_status?: string
    new_status?: string
    udid?: string
    name?: string
  }
}

export interface JobProgressUpdate extends WebSocketMessage {
  type: 'job_progress_update'
  job_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: {
    old_status?: string
    new_status?: string
    batch_id?: string
    device_udid?: string
    execution_time?: number
    result?: any
    error_message?: string
  }
}

export interface SystemNotification extends WebSocketMessage {
  type: 'system_notification'
  notification_type: string
  message: string
  data: Record<string, any>
}

export interface HeartbeatMessage extends WebSocketMessage {
  type: 'heartbeat'
  active_connections: number
}

export interface ConnectionEstablished extends WebSocketMessage {
  type: 'connection_established'
  message: string
}

// WebSocket connection states
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error'

// Global WebSocket connection manager to prevent multiple connections
class WebSocketManager {
  private static instance: WebSocketManager
  private globalConnection: WebSocket | null = null
  private subscribers: Set<(message: WebSocketMessage) => void> = new Set()
  private connectionState: WebSocketState = 'disconnected'
  private stateSubscribers: Set<(state: WebSocketState) => void> = new Set()

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager()
    }
    return WebSocketManager.instance
  }

  connect(url: string): void {
    if (this.globalConnection?.readyState === WebSocket.OPEN || 
        this.globalConnection?.readyState === WebSocket.CONNECTING) {
      console.log('Global WebSocket already connected or connecting')
      return
    }

    if (this.globalConnection) {
      this.globalConnection.close()
    }

    this.setConnectionState('connecting')
    console.log('Creating global WebSocket connection to:', url)
    
    this.globalConnection = new WebSocket(url)
    
    this.globalConnection.onopen = () => {
      console.log('Global WebSocket connection opened')
      this.setConnectionState('connected')
      
      // Subscribe to all updates by default
      this.globalConnection?.send(JSON.stringify({
        type: 'subscribe',
        subscription_type: 'all'
      }))
    }
    
    this.globalConnection.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        this.broadcastMessage(message)
      } catch (error) {
        console.error('Failed to parse global WebSocket message:', error)
      }
    }
    
    this.globalConnection.onclose = (event) => {
      console.log('Global WebSocket connection closed:', event.code, event.reason)
      this.setConnectionState('disconnected')
    }
    
    this.globalConnection.onerror = (error) => {
      console.error('Global WebSocket error:', error)
      this.setConnectionState('error')
    }
  }

  disconnect(): void {
    if (this.globalConnection) {
      this.globalConnection.close()
      this.globalConnection = null
    }
    this.setConnectionState('disconnected')
  }

  subscribe(callback: (message: WebSocketMessage) => void): () => void {
    this.subscribers.add(callback)
    return () => this.subscribers.delete(callback)
  }

  subscribeToState(callback: (state: WebSocketState) => void): () => void {
    this.stateSubscribers.add(callback)
    return () => this.stateSubscribers.delete(callback)
  }

  private broadcastMessage(message: WebSocketMessage): void {
    this.subscribers.forEach(callback => callback(message))
  }

  private setConnectionState(state: WebSocketState): void {
    this.connectionState = state
    this.stateSubscribers.forEach(callback => callback(state))
  }

  getConnectionState(): WebSocketState {
    return this.connectionState
  }

  send(message: Record<string, any>): void {
    if (this.globalConnection?.readyState === WebSocket.OPEN) {
      this.globalConnection.send(JSON.stringify(message))
    }
  }
}

// Hook options
export interface UseWebSocketOptions {
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  const [state, setState] = useState<WebSocketState>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionStats, setConnectionStats] = useState<{ active_connections: number }>({ active_connections: 0 })
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const queryClient = useQueryClient()
  const manager = useRef(WebSocketManager.getInstance())

  // Get WebSocket URL from environment
  const getWebSocketUrl = useCallback(() => {
    let wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws'
    
    // Use the correct backend URL for production
    if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
      wsUrl = 'wss://fsn-system-backend.onrender.com/api/v1/ws'
    } else if (typeof window !== 'undefined' && window.location.protocol === 'https:' && wsUrl.startsWith('ws://')) {
      // Auto-convert ws:// to wss:// when running on HTTPS
      wsUrl = wsUrl.replace('ws://', 'wss://')
    }
    
    const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    return `${wsUrl}?client_id=${clientId}`
  }, [])

  // Connect to WebSocket using global manager
  const connect = useCallback(() => {
    const wsUrl = getWebSocketUrl()
    manager.current.connect(wsUrl)
  }, [getWebSocketUrl])

  // Subscribe to global WebSocket messages
  useEffect(() => {
    const unsubscribe = manager.current.subscribe((message) => {
      setLastMessage(message)
      onMessage?.(message)
      handleWebSocketMessage(message)
    })

    return unsubscribe
  }, [onMessage])

  // Subscribe to global WebSocket state changes
  useEffect(() => {
    const unsubscribe = manager.current.subscribeToState((newState) => {
      setState(newState)
      
      if (newState === 'connected') {
        reconnectAttemptsRef.current = 0
        onConnect?.()
      } else if (newState === 'disconnected') {
        onDisconnect?.()
        
        // Auto-reconnect if not manually disconnected
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          console.log(`Attempting to reconnect in ${reconnectInterval}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++
            connect()
          }, reconnectInterval)
        }
      } else if (newState === 'error') {
        onError?.(new Event('WebSocket error'))
      }
    })

    return unsubscribe
  }, [onConnect, onDisconnect, onError, connect, reconnectInterval, maxReconnectAttempts])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    manager.current.disconnect()
  }, [])

  // Send message to WebSocket
  const sendMessage = useCallback((message: Record<string, any>) => {
    manager.current.send(message)
  }, [])

  // Ping the server
  const ping = useCallback(() => {
    sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }, [sendMessage])

  // Subscribe to specific updates
  const subscribe = useCallback((subscriptionType: 'devices' | 'jobs' | 'system' | 'all') => {
    sendMessage({
      type: 'subscribe',
      subscription_type: subscriptionType
    })
  }, [sendMessage])

  // Get current system status
  const getStatus = useCallback(() => {
    sendMessage({
      type: 'get_status'
    })
  }, [sendMessage])

  // Handle different WebSocket message types
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'device_status_update':
        handleDeviceStatusUpdate(message as DeviceStatusUpdate)
        break
      case 'job_progress_update':
        handleJobProgressUpdate(message as JobProgressUpdate)
        break
      case 'job_update':
        // Let job_update messages pass through to component handlers
        console.log('📊 JOB_UPDATE MESSAGE RECEIVED:', JSON.stringify(message, null, 2))
        console.log('📊 Passing job_update to component handlers')
        // Don't consume the message - let components handle it
        break
      case 'system_notification':
        handleSystemNotification(message as SystemNotification)
        break
      case 'heartbeat':
        handleHeartbeat(message as HeartbeatMessage)
        break
      case 'connection_established':
        handleConnectionEstablished(message as ConnectionEstablished)
        break
      case 'pong':
        // Handle pong response
        break
      case 'subscription_confirmed':
        // Handle subscription confirmation
        console.log('WebSocket subscription confirmed:', message)
        break
      default:
        console.log('Unknown WebSocket message type:', message.type)
    }
  }, [])

  // Handle device status updates
  const handleDeviceStatusUpdate = useCallback((message: DeviceStatusUpdate) => {
    // Invalidate device queries to trigger refetch
    queryClient.invalidateQueries({ queryKey: ['devices'] })
    
    // Show toast notification
    const { device_id, status, details } = message
    const deviceName = details.name || `Device ${device_id}`
    
    if (status === 'active') {
      toast.success(`${deviceName} is now online`, {
        description: `Device ${details.udid} connected successfully`
      })
    } else if (status === 'offline') {
      toast.warning(`${deviceName} went offline`, {
        description: `Device ${details.udid} disconnected`
      })
    } else if (status === 'error') {
      toast.error(`${deviceName} encountered an error`, {
        description: `Device ${details.udid} has an issue`
      })
    }
  }, [queryClient])

  // Handle job progress updates
  const handleJobProgressUpdate = useCallback((message: JobProgressUpdate) => {
    // Invalidate job queries to trigger refetch
    queryClient.invalidateQueries({ queryKey: ['jobs'] })
    
    // Show toast notification
    const { job_id, status, progress } = message
    
    if (status === 'running') {
      toast.info(`Job ${job_id} started`, {
        description: `Running on device ${progress.device_udid}`
      })
    } else if (status === 'completed') {
      toast.success(`Job ${job_id} completed`, {
        description: `Execution time: ${progress.execution_time?.toFixed(2)}s`
      })
    } else if (status === 'failed') {
      toast.error(`Job ${job_id} failed`, {
        description: progress.error_message || 'Unknown error occurred'
      })
    }
  }, [queryClient])

  // Handle system notifications
  const handleSystemNotification = useCallback((message: SystemNotification) => {
    const { notification_type, message: notificationMessage, data } = message
    
    // Show appropriate toast based on notification type
    switch (notification_type) {
      case 'error':
        toast.error(notificationMessage, {
          description: data.description
        })
        break
      case 'warning':
        toast.warning(notificationMessage, {
          description: data.description
        })
        break
      case 'info':
        toast.info(notificationMessage, {
          description: data.description
        })
        break
      case 'success':
        toast.success(notificationMessage, {
          description: data.description
        })
        break
      default:
        toast(notificationMessage, {
          description: data.description
        })
    }
  }, [])

  // Handle heartbeat messages
  const handleHeartbeat = useCallback((message: HeartbeatMessage) => {
    setConnectionStats({
      active_connections: message.active_connections
    })
  }, [])

  // Handle connection established
  const handleConnectionEstablished = useCallback((message: ConnectionEstablished) => {
    toast.success('Connected to real-time updates', {
      description: message.message
    })
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect()
    }
    
    return () => {
      // Don't disconnect on unmount as other components might be using the global connection
      // The global manager will handle cleanup when all subscribers are gone
    }
  }, [autoConnect, connect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    state,
    lastMessage,
    connectionStats,
    connect,
    disconnect,
    sendMessage,
    ping,
    subscribe,
    getStatus,
    isConnected: state === 'connected',
    isConnecting: state === 'connecting',
    isDisconnected: state === 'disconnected',
    hasError: state === 'error'
  }
}

// Hook for device-specific WebSocket updates
export function useDeviceWebSocket(deviceId?: number) {
  const { subscribe, ...websocket } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'device_status_update' && 
          (message as DeviceStatusUpdate).device_id === deviceId) {
        // Handle device-specific updates
      }
    }
  })

  useEffect(() => {
    if (deviceId) {
      subscribe('devices')
    }
  }, [deviceId, subscribe])

  return websocket
}

// Hook for job-specific WebSocket updates
export function useJobWebSocket(jobId?: number) {
  const { subscribe, ...websocket } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'job_progress_update' && 
          (message as JobProgressUpdate).job_id === jobId) {
        // Handle job-specific updates
      }
    }
  })

  useEffect(() => {
    if (jobId) {
      subscribe('jobs')
    }
  }, [jobId, subscribe])

  return websocket
}
