"use client"

// @ts-ignore
import React, { useState, useEffect } from "react"

// Type definitions for JSX
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
// @ts-ignore
import { Loader2, CheckCircle, XCircle, Key, Sparkles } from "lucide-react"
import Image from "next/image"

interface LicenseValidationProps {
  onLicenseValid: (licenseInfo: any) => void
}

export function LicenseValidation({ onLicenseValid }: LicenseValidationProps) {
  const [licenseKey, setLicenseKey] = useState("")
  const [deviceId, setDeviceId] = useState("")
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState("")
  const [isValid, setIsValid] = useState(false)

  // Auto-generate device ID on component mount
  useEffect(() => {
    const generateDeviceId = () => {
      const deviceId = `device-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      setDeviceId(deviceId)
    }
    generateDeviceId()
  }, [])

  // Generate device ID (simple implementation)
  const generateDeviceId = () => {
    const deviceId = `device-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setDeviceId(deviceId)
  }

  // Validate license against our license server
  const validateLicense = async () => {
    if (!licenseKey.trim()) {
      setError("Please enter a license key")
      return
    }

    // Auto-generate device ID if not present
    if (!deviceId.trim()) {
      const newDeviceId = `device-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      setDeviceId(newDeviceId)
    }

    setIsValidating(true)
    setError("")

    try {
      const apiUrl = "/api/license/validate";
      console.log('🔍 Using internal API route:', apiUrl);
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          license_key: licenseKey.trim(),
          device_id: deviceId.trim(),
        }),
      })

      const data = await response.json()

      if (response.ok && data.valid) {
        setIsValid(true)
        // Store license info in localStorage
        localStorage.setItem("fsn_license", JSON.stringify({
          licenseKey: licenseKey.trim(),
          deviceId: deviceId.trim(),
          platforms: data.platforms,
          licenseType: data.license_type,
          expiresAt: data.expires_at,
          maxDevices: data.max_devices,
          currentDevices: data.current_devices,
          validatedAt: new Date().toISOString(),
        }))
        
        // Call the callback to proceed to main app
        setTimeout(() => {
          onLicenseValid(data)
        }, 1000)
      } else {
        setError(data.error || "Invalid license key")
      }
    } catch (err) {
      setError("Failed to validate license. Please check your connection.")
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <Card className="w-full max-w-md border border-gray-800 bg-white shadow-2xl">
        <CardHeader className="text-center pb-8">
          <div className="mx-auto mb-6 w-20 h-20 bg-black rounded-2xl flex items-center justify-center shadow-lg">
            <Image 
              src="/fusion.png" 
              alt="Fusion Logo" 
              width={48} 
              height={48}
              className="rounded-lg"
            />
          </div>
          <CardDescription className="text-gray-600 mt-2">
            Enter your license key to access the automation platform
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6 px-8 pb-8">
          {isValid ? (
            <div className="text-center space-y-6">
              <div className="mx-auto w-20 h-20 bg-black rounded-full flex items-center justify-center shadow-lg">
                <CheckCircle className="w-10 h-10 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-black">License Validated!</h3>
                <p className="text-sm text-gray-600">Redirecting to the main application...</p>
              </div>
              <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                <Sparkles className="w-4 h-4" />
                <span>Welcome</span>
              </div>
            </div>
          ) : (
            <>
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="licenseKey" className="text-sm font-medium text-black flex items-center gap-2">
                    <Key className="w-4 h-4" />
                    License Key
                  </Label>
                  <Input
                    id="licenseKey"
                    type="password"
                    placeholder="Enter your license key"
                    value={licenseKey}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLicenseKey(e.target.value)}
                    className="h-12 text-center font-mono tracking-wider border-2 border-gray-300 focus:border-black focus:ring-black/20 transition-all duration-200"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        validateLicense()
                      }
                    }}
                  />
                </div>
              </div>

              {error && (
                <Alert variant="destructive" className="border-red-200 bg-red-50">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription className="text-red-700">{error}</AlertDescription>
                </Alert>
              )}

              <Button
                onClick={validateLicense}
                disabled={isValidating || !licenseKey.trim()}
                className="w-full h-12 bg-black hover:bg-gray-800 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Validating License...
                  </>
                ) : (
                  <>
                    <Key className="w-5 h-5 mr-2" />
                    Validate License
                  </>
                )}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
