"use client"

// @ts-ignore
import React, { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { setLicenseContext } from "@/lib/services/license-api-service"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"

// Use internal API route to avoid mixed content issues
const getLicenseApiUrl = () => {
  // Use internal API route that proxies to license server
  return "/api/license/validate";
}

interface LicenseInfo {
  licenseKey: string
  deviceId: string
  platforms: string[]
  licenseType: string
  expiresAt: string | null
  maxDevices: number | string
  currentDevices: number
  validatedAt: string
}

interface LicenseContextType {
  license: LicenseInfo | null
  isValid: boolean
  isLoading: boolean
  validateLicense: (licenseKey: string, deviceId: string) => Promise<boolean>
  clearLicense: () => void
  refreshLicense: () => Promise<void>
  updateDeviceCount: () => void
}

const LicenseContext = createContext<LicenseContextType | undefined>(undefined)

export function useLicense() {
  const context = useContext(LicenseContext)
  if (context === undefined) {
    throw new Error("useLicense must be used within a LicenseProvider")
  }
  return context
}

interface LicenseProviderProps {
  children: ReactNode
}

export function LicenseProvider({ children }: LicenseProviderProps) {
  console.log('🚀 LICENSE PROVIDER - Component initializing')
  const [license, setLicense] = useState<LicenseInfo | null>(null)
  const [isValid, setIsValid] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Load license from localStorage on mount
  useEffect(() => {
    console.log('🚀 LICENSE PROVIDER - useEffect running')
    const loadLicense = () => {
      console.log('🚀 LICENSE PROVIDER - loadLicense function called')
      try {
        const storedLicense = localStorage.getItem("fsn_license")
        console.log("🔍 Loading license from localStorage:", storedLicense)
        if (storedLicense) {
          const licenseData = JSON.parse(storedLicense)
          console.log("🔍 Parsed license data:", licenseData)
          console.log("🔍 License maxDevices:", licenseData.maxDevices)
          console.log("🔍 License maxDevices type:", typeof licenseData.maxDevices)
          
          // Fix null maxDevices to 'unlimited'
          if (licenseData.maxDevices === null) {
            console.log("🔧 Fixing null maxDevices to 'unlimited'")
            licenseData.maxDevices = 'unlimited'
            localStorage.setItem("fsn_license", JSON.stringify(licenseData))
          }
          
          setLicense(licenseData)
          setIsValid(true)
          
          // Initialize license-aware storage
          licenseAwareStorageService.initialize(licenseData.licenseKey)
          
          // Set license context for API calls
          setLicenseContext(licenseData.licenseKey, licenseData.deviceId)
          console.log('🔐 LICENSE PROVIDER - Set license context:', { licenseKey: licenseData.licenseKey, deviceId: licenseData.deviceId })
          
          // Validate and migrate data after license is set
          licenseAwareStorageService.validateAndMigrateData().catch(console.error)
        } else {
          // No license found - user needs to validate
          console.log("🔍 No stored license found - user needs to validate")
          setLicense(null)
          setIsValid(false)
        }
      } catch (error) {
        console.error("Failed to load license from localStorage:", error)
        localStorage.removeItem("fsn_license")
        setLicense(null)
        setIsValid(false)
      } finally {
        setIsLoading(false)
      }
    }

    loadLicense()
  }, [])

  const validateLicense = async (licenseKey: string, deviceId: string): Promise<boolean> => {
    try {
      const apiUrl = getLicenseApiUrl();
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-cache",
          "Pragma": "no-cache",
        },
        body: JSON.stringify({
          license_key: licenseKey.trim(),
          device_id: deviceId.trim(),
        }),
      })

      const data = await response.json()

      if (response.ok && data.valid) {
        // Get actual device count from local API instead of remote server
        let actualDeviceCount = 0
        try {
          const deviceResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          })
          if (deviceResponse.ok) {
            const deviceData = await deviceResponse.json()
            actualDeviceCount = deviceData.devices ? deviceData.devices.length : 0
          }
        } catch (error) {
          console.warn('Failed to get local device count, using 0:', error)
        }

        const licenseInfo: LicenseInfo = {
          licenseKey: licenseKey.trim(),
          deviceId: deviceId.trim(),
          platforms: data.platforms,
          licenseType: data.license_type,
          expiresAt: data.expires_at,
          maxDevices: (data.max_devices === -1 || data.max_devices === null) ? 'unlimited' : Number(data.max_devices),
          currentDevices: actualDeviceCount, // Use local device count
          validatedAt: new Date().toISOString(),
        }

        console.log("🔍 Setting license from validation:", licenseInfo)
        console.log("🔍 Validation maxDevices:", licenseInfo.maxDevices)
        console.log("🔍 Validation maxDevices type:", typeof licenseInfo.maxDevices)
        setLicense(licenseInfo)
        setIsValid(true)
        localStorage.setItem("fsn_license", JSON.stringify(licenseInfo))
        
        // Initialize license-aware storage
        licenseAwareStorageService.initialize(licenseKey.trim())
        
        // Set license context for API calls
        setLicenseContext(licenseKey.trim(), deviceId.trim())
        
        return true
      } else {
        console.log("❌ License validation failed:", data.error)
        setLicense(null)
        setIsValid(false)
        return false
      }
    } catch (error) {
      console.error("License validation failed:", error)
      setLicense(null)
      setIsValid(false)
      return false
    }
  }

  const clearLicense = () => {
    setLicense(null)
    setIsValid(false)
    localStorage.removeItem("fsn_license")
  }

  const refreshLicense = async () => {
    if (!license) return

    try {
      const apiUrl = getLicenseApiUrl();
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-cache",
          "Pragma": "no-cache",
        },
        body: JSON.stringify({
          license_key: license.licenseKey,
          device_id: license.deviceId,
        }),
      })

      const data = await response.json()

      if (response.ok && data.valid) {
        // Get actual device count from local API instead of remote server
        let actualDeviceCount = 0
        try {
          const deviceResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          })
          if (deviceResponse.ok) {
            const deviceData = await deviceResponse.json()
            actualDeviceCount = deviceData.devices ? deviceData.devices.length : 0
          }
        } catch (error) {
          console.warn('Failed to get local device count, using 0:', error)
        }

        const updatedLicense: LicenseInfo = {
          ...license,
          platforms: data.platforms,
          licenseType: data.license_type,
          expiresAt: data.expires_at,
          maxDevices: (data.max_devices === -1 || data.max_devices === null) ? 'unlimited' : Number(data.max_devices),
          currentDevices: actualDeviceCount, // Use local device count
          validatedAt: new Date().toISOString(),
        }

        setLicense(updatedLicense)
        setIsValid(true)
        localStorage.setItem("fsn_license", JSON.stringify(updatedLicense))
      } else {
        clearLicense()
      }
    } catch (error) {
      console.error("License refresh failed:", error)
      clearLicense()
    }
  }

  const updateDeviceCount = async () => {
    if (!license) return

    try {
      // Get actual device count from API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        const actualDeviceCount = data.devices ? data.devices.length : 0

        // Update license with new device count
        const updatedLicense: LicenseInfo = {
          ...license,
          currentDevices: actualDeviceCount,
        }

        setLicense(updatedLicense)
        localStorage.setItem("fsn_license", JSON.stringify(updatedLicense))
      } else {
        console.error('Failed to fetch devices for count update')
      }
    } catch (error) {
      console.error('Error updating device count:', error)
    }
  }

  const value: LicenseContextType = {
    license,
    isValid,
    isLoading,
    validateLicense,
    clearLicense,
    refreshLicense,
    updateDeviceCount,
  }

  return (
    <LicenseContext.Provider value={value}>
      {children}
    </LicenseContext.Provider>
  )
}
