"use client"

import { useLicense } from "@/lib/providers/license-provider"
import { useRouter } from "next/navigation"
import { useCallback } from "react"

interface ProtectedApiOptions {
  requireLicense?: boolean
  platform?: 'instagram' | 'threads'
  action?: string
}

export function useProtectedApi() {
  const { isValid, license, validateLicense } = useLicense()
  const router = useRouter()

  const protectedCall = useCallback(async <T>(
    apiCall: () => Promise<T>,
    options: ProtectedApiOptions = {}
  ): Promise<T> => {
    const { requireLicense = true, platform, action = "perform this action" } = options

    if (!requireLicense) {
      return apiCall()
    }

    // Check if license is valid
    if (!isValid || !license) {
      localStorage.removeItem("fsn_license")
      router.push("/")
      throw new Error("License required")
    }

    // Check if license is expired
    if (license.expiresAt && new Date(license.expiresAt) < new Date()) {
      localStorage.removeItem("fsn_license")
      router.push("/")
      throw new Error("License expired")
    }

    // Check platform access
    if (platform && !license.platforms.includes(platform) && !license.platforms.includes('both')) {
      throw new Error(`License does not include ${platform} platform access`)
    }

    // Validate license for critical actions
    if (action.includes("job") || action.includes("warmup") || action.includes("account")) {
      try {
        const isValidRefresh = await validateLicense(license.licenseKey, license.deviceId)
        if (!isValidRefresh) {
          localStorage.removeItem("fsn_license")
          router.push("/")
          throw new Error("License validation failed")
        }
      } catch (error) {
        console.error("License validation failed:", error)
        localStorage.removeItem("fsn_license")
        router.push("/")
        throw new Error("License validation failed")
      }
    }

    return apiCall()
  }, [isValid, license, validateLicense, router])

  return { protectedCall }
}
