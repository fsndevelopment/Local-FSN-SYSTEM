/**
 * Real-Time Status Component
 * 
 * Displays WebSocket connection status and real-time statistics
 * in the topbar or sidebar for monitoring system health.
 */

'use client'

import React, { useState, useEffect } from 'react'
import { useConnectionStatus } from '@/lib/providers/websocket-provider'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Wifi, 
  WifiOff, 
  AlertCircle, 
  Loader2, 
  Users,
  Activity
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface RealTimeStatusProps {
  className?: string
  showDetails?: boolean
  variant?: 'compact' | 'detailed'
}

// Client-side only wrapper to prevent hydration mismatches
function ClientOnly({ children }: { children: React.ReactNode }) {
  const [hasMounted, setHasMounted] = useState(false)

  useEffect(() => {
    setHasMounted(true)
  }, [])

  if (!hasMounted) {
    // Return a placeholder that matches the initial server render
    return (
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="flex items-center gap-1">
          <WifiOff className="w-4 h-4" />
          <span className="text-xs">Disconnected</span>
        </Badge>
      </div>
    )
  }

  return <>{children}</>
}

export function RealTimeStatus({ 
  className, 
  showDetails = false, 
  variant = 'compact' 
}: RealTimeStatusProps) {
  const { 
    state, 
    isConnected, 
    isConnecting, 
    hasError, 
    activeConnections,
    statusText,
    statusColor 
  } = useConnectionStatus()

  const getStatusIcon = () => {
    if (isConnecting) {
      return <Loader2 className="w-4 h-4 animate-spin" />
    }
    if (isConnected) {
      return <Wifi className="w-4 h-4" />
    }
    if (hasError) {
      return <AlertCircle className="w-4 h-4" />
    }
    return <WifiOff className="w-4 h-4" />
  }

  const getStatusVariant = () => {
    if (isConnected) return 'default'
    if (isConnecting) return 'secondary'
    if (hasError) return 'destructive'
    return 'outline'
  }

  const content = variant === 'compact' ? (
    <div className={cn('flex items-center gap-2', className)}>
      <Badge variant={getStatusVariant()} className="flex items-center gap-1">
        {getStatusIcon()}
        <span className="text-xs">{statusText}</span>
      </Badge>
      {showDetails && isConnected && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Users className="w-3 h-3" />
          <span>{activeConnections}</span>
        </div>
      )}
    </div>
  ) : (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className={cn('text-sm font-medium', statusColor)}>
            {statusText}
          </span>
        </div>
        {isConnected && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Users className="w-3 h-3" />
            <span>{activeConnections} connected</span>
          </div>
        )}
      </div>
      
      {showDetails && (
        <div className="space-y-1 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Activity className="w-3 h-3" />
            <span>Real-time updates</span>
            <Badge variant={isConnected ? 'default' : 'outline'} className="text-xs">
              {isConnected ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </div>
      )}
    </div>
  )

  return <ClientOnly>{content}</ClientOnly>
}

// Compact status indicator for topbar
export function RealTimeStatusIndicator({ className }: { className?: string }) {
  return (
    <RealTimeStatus 
      className={className}
      variant="compact"
      showDetails={false}
    />
  )
}

// Detailed status panel for sidebar or dashboard
export function RealTimeStatusPanel({ className }: { className?: string }) {
  return (
    <RealTimeStatus 
      className={className}
      variant="detailed"
      showDetails={true}
    />
  )
}

// Connection status with manual controls
export function RealTimeStatusControls({ className }: { className?: string }) {
  const { connect, disconnect, ping, getStatus, isConnected, isConnecting } = useConnectionStatus()

  return (
    <div className={cn('space-y-3', className)}>
      <RealTimeStatusPanel />
      
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={isConnected ? disconnect : connect}
          disabled={isConnecting}
        >
          {isConnected ? 'Disconnect' : 'Connect'}
        </Button>
        
        <Button
          size="sm"
          variant="outline"
          onClick={ping}
          disabled={!isConnected}
        >
          Ping
        </Button>
        
        <Button
          size="sm"
          variant="outline"
          onClick={getStatus}
          disabled={!isConnected}
        >
          Get Status
        </Button>
      </div>
    </div>
  )
}
