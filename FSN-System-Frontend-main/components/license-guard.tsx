"use client"

import { useLicense } from "@/lib/providers/license-provider"
import { LicenseValidation } from "@/components/license-validation"
import { Loader2 } from "lucide-react"

interface LicenseGuardProps {
  children: React.ReactNode
}

export function LicenseGuard({ children }: LicenseGuardProps) {
  const { isValid, isLoading, validateLicense } = useLicense()

  const handleLicenseValid = (licenseInfo: any) => {
    // License is already validated and stored by the LicenseValidation component
    // Force a re-render by refreshing the page
    window.location.reload()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
          <p className="text-gray-600">Loading license information...</p>
        </div>
      </div>
    )
  }

  if (!isValid) {
    return <LicenseValidation onLicenseValid={handleLicenseValid} />
  }

  return <>{children}</>
}
