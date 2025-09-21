"use client"

import { useLicense } from "@/lib/providers/license-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Shield, Lock, AlertTriangle, RefreshCw } from "lucide-react"
import { ReactNode, useEffect } from "react"

interface LicenseBlockerProps {
  children: ReactNode
  platform?: 'instagram' | 'threads'
  action?: string
  fallback?: ReactNode
}

export function LicenseBlocker({ 
  children, 
  platform, 
  action = "perform this action",
  fallback 
}: LicenseBlockerProps) {
  const { isValid, license, isLoading, refreshLicense, clearLicense } = useLicense()

  // Refresh license periodically to catch deletions
  useEffect(() => {
    if (isValid && license) {
      const interval = setInterval(() => {
        refreshLicense()
      }, 30000) // Check every 30 seconds

      return () => clearInterval(interval)
    }
  }, [isValid, license, refreshLicense])

  // Show loading state
  if (isLoading) {
    return (
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-blue-700">Loading license information...</p>
        </CardContent>
      </Card>
    )
  }

  // No license - show license required
  if (!isValid || !license) {
    if (fallback) return <>{fallback}</>

    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-amber-600" />
            <CardTitle className="text-amber-800">License Required</CardTitle>
          </div>
          <CardDescription className="text-amber-700">
            A valid license is required to {action}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-amber-700 mb-4">
            Please enter your license key to access this feature.
          </p>
          <Button 
            onClick={() => window.location.reload()}
            className="w-full"
          >
            Enter License Key
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Check if license is expired
  if (license.expiresAt && new Date(license.expiresAt) < new Date()) {
    if (fallback) return <>{fallback}</>

    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <CardTitle className="text-red-800">License Expired</CardTitle>
          </div>
          <CardDescription className="text-red-700">
            Your license has expired and needs to be renewed.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-700 mb-4">
            Expired on: {new Date(license.expiresAt).toLocaleDateString()}
          </p>
          <Button 
            onClick={() => window.location.reload()}
            className="w-full"
          >
            Enter New License
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Check platform access
  if (platform && !license.platforms.includes(platform) && !license.platforms.includes('both')) {
    if (fallback) return <>{fallback}</>

    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Lock className="w-5 h-5 text-red-600" />
            <CardTitle className="text-red-800">Platform Not Included</CardTitle>
          </div>
          <CardDescription className="text-red-700">
            Your license does not include {platform} platform access.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-700 mb-4">
            Upgrade your license to access {platform} features.
          </p>
          <Button 
            onClick={() => window.location.reload()}
            className="w-full"
          >
            Enter New License
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Check device limit - only block when exceeding the limit, not when at the limit
  // Also ensure we have valid data before checking limits
  if (license.maxDevices !== 'unlimited' && 
      license.maxDevices !== -1 && 
      typeof license.maxDevices === 'number' && 
      typeof license.currentDevices === 'number' &&
      license.currentDevices > license.maxDevices) {
    if (fallback) return <>{fallback}</>

    return (
      <Card className="border-orange-200 bg-orange-50">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <CardTitle className="text-orange-800">Device Limit Reached</CardTitle>
          </div>
          <CardDescription className="text-orange-700">
            You have reached the maximum number of devices for your license.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-orange-700 mb-4">
            Current devices: {license.currentDevices} / {license.maxDevices}
          </p>
          <Button 
            onClick={() => window.location.reload()}
            className="w-full"
          >
            Enter New License
          </Button>
        </CardContent>
      </Card>
    )
  }

  // All checks passed, render children
  return <>{children}</>
}
