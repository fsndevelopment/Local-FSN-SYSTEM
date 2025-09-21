"use client"

import { useLicense } from "@/lib/providers/license-provider"
import { useRouter } from "next/navigation"
import { useCallback } from "react"

export function useLicenseProtection() {
  const { isValid, license, validateLicense } = useLicense()
  const router = useRouter()

  const requireLicense = useCallback(async (action: string = "perform this action") => {
    if (!isValid || !license) {
      // Clear any existing license and redirect to validation
      localStorage.removeItem("fsn_license")
      router.push("/")
      return false
    }

    // Check if license is expired
    if (license.expiresAt && new Date(license.expiresAt) < new Date()) {
      localStorage.removeItem("fsn_license")
      router.push("/")
      return false
    }

    // Refresh license validation for critical actions
    if (action.includes("job") || action.includes("warmup") || action.includes("account")) {
      try {
        const isValidRefresh = await validateLicense(license.licenseKey, license.deviceId)
        if (!isValidRefresh) {
          localStorage.removeItem("fsn_license")
          router.push("/")
          return false
        }
      } catch (error) {
        console.error("License validation failed:", error)
        localStorage.removeItem("fsn_license")
        router.push("/")
        return false
      }
    }

    return true
  }, [isValid, license, validateLicense, router])

  const checkPlatformAccess = useCallback((platform: 'instagram' | 'threads') => {
    if (!license) return false
    return license.platforms.includes(platform) || license.platforms.includes('both')
  }, [license])

  const checkDeviceLimit = useCallback(() => {
    if (!license) return false
    if (license.maxDevices === 'unlimited' || license.maxDevices === -1) return true
    return license.currentDevices < (license.maxDevices as number)
  }, [license])

  return {
    requireLicense,
    checkPlatformAccess,
    checkDeviceLimit,
    isValid,
    license
  }
}
