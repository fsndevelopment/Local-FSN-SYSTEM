"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, Smartphone, User, Image as ImageIcon } from "lucide-react"
import { licenseAwareStorageService, LocalDevice } from "@/lib/services/license-aware-storage-service"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { LicenseBlocker } from "@/components/license-blocker"
import { useLicense } from "@/lib/providers/license-provider"
import { useCreateDevice } from "@/lib/hooks/use-devices"

// Model interface
interface Model {
  id: string
  name: string
  profilePhoto?: string
  created_at: string
  updated_at: string
}

export default function AddDevicePage() {
  const router = useRouter()
  const { license, updateDeviceCount } = useLicense()
  const [deviceName, setDeviceName] = useState("")
  const [udid, setUdid] = useState("")
  const [appiumPort, setAppiumPort] = useState("")
  const [wdaPort, setWdaPort] = useState("")
  const [wdaBundleId, setWdaBundleId] = useState("")
  const [jailbroken, setJailbroken] = useState(false)
  const [selectedModel, setSelectedModel] = useState<string>("")
  const [ngrokToken, setNgrokToken] = useState("")
  const [models, setModels] = useState<Model[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [deviceLimitError, setDeviceLimitError] = useState("")
  const [generalError, setGeneralError] = useState("")
  const isSubmittingRef = useRef(false)

  // React Query mutation for device creation
  const createDeviceMutation = useCreateDevice()
  const isLoadingDevice = isLoading || createDeviceMutation.isPending

  // Clear errors when user starts typing
  const clearErrors = () => {
    setGeneralError("")
    setDeviceLimitError("")
  }

  // Load models from license-aware storage
  const loadModels = useCallback(async () => {
    try {
      const savedModels = await licenseAwareStorageService.getModels()
      setModels(savedModels)
    } catch (error) {
      console.error('Failed to load models:', error)
      setModels([])
    }
  }, [])

  useEffect(() => {
    loadModels()
  }, [loadModels])

  // Refresh models when page becomes visible (in case models were added in another tab)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadModels()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [loadModels])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Prevent double submission using ref
    if (isSubmittingRef.current || isLoadingDevice || isLoading) {
      console.log('🚫 Form submission already in progress, ignoring duplicate submission', {
        isSubmittingRef: isSubmittingRef.current,
        isLoadingDevice,
        isLoading
      })
      return
    }
    
    console.log('🚀 Starting form submission')
    isSubmittingRef.current = true
    setIsLoading(true)
    setDeviceLimitError("")

    try {
      // Check device limit before creating device
      console.log('License object:', license)
      console.log('License maxDevices:', license?.maxDevices)
      console.log('License maxDevices type:', typeof license?.maxDevices)
      console.log('License maxDevices === "unlimited":', license?.maxDevices === 'unlimited')
      
      if (license && license.maxDevices !== 'unlimited') {
        // Use API devices count instead of local storage
        const currentDevices = license.currentDevices || 0
        const maxDevices = Number(license.maxDevices)
        
        console.log('Device limit check:', { 
          currentDevices, 
          maxDevices, 
          license: license.maxDevices,
          localDevices: licenseAwareStorageService.getDevices().length
        })
        
        // Check if adding one more device would exceed the limit
        if (currentDevices + 1 > maxDevices) {
          setDeviceLimitError(`Device limit reached. You can only have ${maxDevices} devices with your current license.`)
          setIsLoading(false)
          return
        }
      } else {
        console.log('Device limit check skipped - unlimited license or no license')
      }

      // Get selected model name
      const selectedModelData = models.find(model => model.id === selectedModel)
      const modelName = selectedModelData ? selectedModelData.name : 'No Model Selected'

      // Create device data for API - only send required fields
      const deviceData = {
        name: deviceName,
        udid: udid,
        platform: 'iOS', // Add required platform field
        // Optional fields with proper defaults
        ios_version: '17.2.1',
        model: modelName || 'iPhone',
        appium_port: parseInt(appiumPort || '4720'),
        wda_port: parseInt(wdaPort || '8100'),
        mjpeg_port: Math.floor(9100 + Math.random() * 1000),
        wda_bundle_id: wdaBundleId || 'com.device.wd',
        jailbroken: jailbroken,
        ngrok_token: ngrokToken || undefined,  // Include ngrok token if provided
        settings: {
          autoAcceptAlerts: true,
          autoDismissAlerts: true,
          shouldTerminateApp: true,
          jailbroken: jailbroken
        }
      }
      
      // Create device using React Query mutation
      console.log('🔄 Calling createDeviceMutation.mutateAsync with data:', deviceData)
      const createdDevice = await createDeviceMutation.mutateAsync(deviceData)
      console.log('✅ Device created via API:', createdDevice)
      
      // Add device to license-aware storage for account cards
      const localDevice: LocalDevice = {
        id: createdDevice.id,
        name: createdDevice.name,
        udid: createdDevice.udid,
        ios_version: createdDevice.ios_version,
        model: createdDevice.model,
        appium_port: createdDevice.appium_port,
        wda_port: createdDevice.wda_port,
        mjpeg_port: createdDevice.mjpeg_port,
        wda_bundle_id: createdDevice.wda_bundle_id,
        jailbroken: createdDevice.jailbroken,
        status: createdDevice.status,
        created_at: createdDevice.created_at,
        updated_at: createdDevice.updated_at
      }
      licenseAwareStorageService.addDevice(localDevice)
      console.log('✅ Device added to license-aware storage:', localDevice)
      
      // Update device count in license
      updateDeviceCount()
      
      console.log("Device added successfully:", { deviceName, udid })
      
      // Show success popup
      setSuccessMessage("Device added successfully!")
      setShowSuccess(true)
      
      // Redirect back to devices page after a short delay
      setTimeout(() => {
        router.push('/devices')
      }, 1500)
    } catch (error: any) {
      console.error("Failed to add device:", error)
      
      // Handle different types of errors
      if (error?.detail) {
        if (Array.isArray(error.detail)) {
          // Handle validation errors array
          const validationErrors = error.detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join(', ')
          setGeneralError(`Validation errors: ${validationErrors}`)
        } else if (typeof error.detail === 'string') {
          if (error.detail.includes("UDID already exists")) {
            setGeneralError("A device with this UDID already exists. Please use a different UDID.")
          } else if (error.detail.includes("Device limit")) {
            setDeviceLimitError(error.detail)
          } else {
            setGeneralError(error.detail)
          }
        } else {
          setGeneralError("Validation failed. Please check your input.")
        }
      } else if (error?.message) {
        setGeneralError(error.message)
      } else {
        setGeneralError("Failed to add device. Please try again.")
      }
    } finally {
      setIsLoading(false)
      isSubmittingRef.current = false
    }
  }

  return (
    <LicenseBlocker action="add new devices">
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          onClick={() => router.back()}
          variant="outline"
          size="sm"
          className="rounded-full"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Add New Device</h1>
          <p className="text-muted-foreground">Connect a new iPhone to your farm</p>
        </div>
      </div>

      {/* Add Device Form */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Smartphone className="w-5 h-5 mr-2" />
            Device Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          {deviceLimitError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{deviceLimitError}</p>
            </div>
          )}
          {generalError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{generalError}</p>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="deviceName">Device Name</Label>
              <Input
                id="deviceName"
                type="text"
                placeholder="e.g., iPhone 15 Pro - Device 1"
                value={deviceName}
                onChange={(e) => {
                  setDeviceName(e.target.value)
                  clearErrors()
                }}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="udid">Device UDID</Label>
              <Input
                id="udid"
                type="text"
                placeholder="e.g., 00008030-001A14E40C38802E"
                value={udid}
                onChange={(e) => {
                  setUdid(e.target.value)
                  clearErrors()
                }}
                required
              />
              <p className="text-xs text-muted-foreground">
                You can find the UDID in Xcode → Window → Devices and Simulators
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ngrokToken">ngrok Token (Optional)</Label>
              <Input
                id="ngrokToken"
                type="text"
                placeholder="e.g., 2abc123def456_your_ngrok_token_here"
                value={ngrokToken}
                onChange={(e) => setNgrokToken(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Required only for photo posting. Get your token from ngrok.com dashboard.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="model">Assigned Model</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={loadModels}
                  className="text-xs"
                >
                  Refresh Models
                </Button>
              </div>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a model for this device" />
                </SelectTrigger>
                <SelectContent>
                  {models.length === 0 ? (
                    <SelectItem value="no-models" disabled>
                      <div className="flex items-center space-x-2">
                        <User className="w-4 h-4" />
                        <span>No models available</span>
                      </div>
                    </SelectItem>
                  ) : (
                    models.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                            {model.profilePhoto ? (
                              <img 
                                src={model.profilePhoto} 
                                alt={model.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <ImageIcon className="w-3 h-3 text-muted-foreground" />
                            )}
                          </div>
                          <span>{model.name}</span>
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Choose which model this device will be assigned to
                {models.length === 0 && (
                  <span className="block mt-1">
                    <Button
                      type="button"
                      variant="link"
                      className="p-0 h-auto text-xs text-blue-600 hover:text-blue-700"
                      onClick={() => router.push('/models/add')}
                    >
                      Create a model first
                    </Button>
                  </span>
                )}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="appiumPort">Appium Port</Label>
                <Input
                  id="appiumPort"
                  type="number"
                  placeholder="4720"
                  value={appiumPort}
                  onChange={(e) => setAppiumPort(e.target.value)}
                  min="1000"
                  max="65535"
                />
                <p className="text-xs text-muted-foreground">
                  Port for Appium server
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="wdaPort">WDA Port</Label>
                <Input
                  id="wdaPort"
                  type="number"
                  placeholder="8100"
                  value={wdaPort}
                  onChange={(e) => setWdaPort(e.target.value)}
                  min="1000"
                  max="65535"
                />
                <p className="text-xs text-muted-foreground">
                  Port for WebDriverAgent
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="wdaBundleId">WDA Bundle ID</Label>
              <Input
                id="wdaBundleId"
                type="text"
                placeholder="com.device1.wd1"
                value={wdaBundleId}
                onChange={(e) => setWdaBundleId(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Unique bundle identifier for WebDriverAgent (e.g., com.device1.wd1)
              </p>
            </div>


            <div className="space-y-2">
              <Label htmlFor="jailbroken">Device Type</Label>
              <Select value={jailbroken ? "true" : "false"} onValueChange={(value) => setJailbroken(value === "true")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select device type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">
                    <div className="flex items-center space-x-2">
                      <span>Non-Jailbroken</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="true">
                    <div className="flex items-center space-x-2">
                      <span>Jailbroken</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Jailbroken devices support Crane containers for account switching
              </p>
            </div>


            <div className="flex space-x-3 pt-4">
              <Button
                type="submit"
                disabled={isLoadingDevice || isSubmittingRef.current}
                className="bg-black text-white hover:bg-neutral-900"
              >
                {isLoadingDevice ? "Adding Device..." : "Add Device"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Setup Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <h4 className="font-medium">1. Enable Developer Mode</h4>
            <p className="text-sm text-muted-foreground">
              On your iPhone: Settings → Privacy & Security → Developer Mode → Enable
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">2. Trust Computer</h4>
            <p className="text-sm text-muted-foreground">
              Connect iPhone to Mac and tap "Trust" when prompted
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">3. Install WebDriverAgent</h4>
            <p className="text-sm text-muted-foreground">
              WebDriverAgent will be automatically installed when you add the device
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Success Popup */}
      <SuccessPopup
        isOpen={showSuccess}
        onClose={() => setShowSuccess(false)}
        title={successMessage}
        autoClose={true}
        duration={3000}
      />
      </div>
    </LicenseBlocker>
  )
}
