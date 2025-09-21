"use client"

import { useLicenseProtection } from "@/lib/hooks/use-license-protection"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, Lock, AlertTriangle } from "lucide-react"
import { ReactNode } from "react"

interface LicenseProtectedProps {
  children: ReactNode
  platform?: 'instagram' | 'threads'
  action?: string
  fallback?: ReactNode
  showLicenseRequired?: boolean
}

export function LicenseProtected({ 
  children, 
  platform, 
  action = "perform this action",
  fallback,
  showLicenseRequired = true 
}: LicenseProtectedProps) {
  const { isValid, license, checkPlatformAccess, checkDeviceLimit } = useLicenseProtection()

  // If no license, show fallback or license required message
  if (!isValid || !license) {
    if (fallback) return <>{fallback}</>
    
    if (!showLicenseRequired) return null

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
          <p className="text-sm text-amber-700">
            Please enter your license key to access this feature.
          </p>
        </CardContent>
      </Card>
    )
  }

  // Check platform access
  if (platform && !checkPlatformAccess(platform)) {
    if (fallback) return <>{fallback}</>
    
    if (!showLicenseRequired) return null

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
          <p className="text-sm text-red-700">
            Upgrade your license to access {platform} features.
          </p>
        </CardContent>
      </Card>
    )
  }

  // Check device limit
  if (!checkDeviceLimit()) {
    if (fallback) return <>{fallback}</>
    
    if (!showLicenseRequired) return null

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
          <p className="text-sm text-orange-700">
            Current devices: {license.currentDevices} / {license.maxDevices === 'unlimited' ? '∞' : license.maxDevices}
          </p>
        </CardContent>
      </Card>
    )
  }

  // Check if license is expired
  if (license.expiresAt && new Date(license.expiresAt) < new Date()) {
    if (fallback) return <>{fallback}</>
    
    if (!showLicenseRequired) return null

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
          <p className="text-sm text-red-700">
            Expired on: {new Date(license.expiresAt).toLocaleDateString()}
          </p>
        </CardContent>
      </Card>
    )
  }

  // All checks passed, render children
  return <>{children}</>
}
