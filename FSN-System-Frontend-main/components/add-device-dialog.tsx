"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Smartphone, User, RefreshCw } from "lucide-react"
import { licenseAwareStorageService, LocalDevice } from "@/lib/services/license-aware-storage-service"
import { SuccessPopup } from "@/components/ui/unified-popup"
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

interface AddDeviceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onDeviceAdded?: () => void
}

export function AddDeviceDialog({ open, onOpenChange, onDeviceAdded }: AddDeviceDialogProps) {
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

  // Reset form
  const resetForm = () => {
    setDeviceName("")
    setUdid("")
    setAppiumPort("")
    setWdaPort("")
    setWdaBundleId("")
    setJailbroken(false)
    setSelectedModel("")
    setNgrokToken("")
    clearErrors()
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
    if (open) {
      loadModels()
      resetForm() // Reset form when dialog opens
    }
  }, [open, loadModels])

  // Refresh models when dialog becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && open) {
        loadModels()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [loadModels, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (isSubmittingRef.current) return
    isSubmittingRef.current = true
    
    try {
      setIsLoading(true)
      clearErrors()

      // Validate required fields
      if (!deviceName.trim()) {
        setGeneralError("Device name is required")
        return
      }

      if (!udid.trim()) {
        setGeneralError("Device UDID is required")
        return
      }

      // Check device limit
      if (license && license.deviceLimit !== -1) {
        const currentDeviceCount = license.deviceCount || 0
        if (currentDeviceCount >= license.deviceLimit) {
          setDeviceLimitError(`Device limit reached (${license.deviceLimit}). Please upgrade your license to add more devices.`)
          return
        }
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
      
      // Close dialog
      onOpenChange(false)
      
      // Notify parent component
      if (onDeviceAdded) {
        onDeviceAdded()
      }
      
    } catch (error: any) {
      console.error("Failed to add device:", error)
      
      // Handle specific error types
      if (error.message?.includes('Device limit')) {
        setDeviceLimitError(error.message)
      } else if (error.message?.includes('UDID already exists')) {
        setGeneralError("A device with this UDID already exists")
      } else if (error.message?.includes('network') || error.message?.includes('fetch')) {
        setGeneralError("Network error. Please check your connection and try again.")
      } else {
        setGeneralError("Failed to add device. Please try again.")
      }
    } finally {
      setIsLoading(false)
      isSubmittingRef.current = false
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent 
          className="!w-[1000px] !h-[700px] !max-w-none !max-h-none bg-white rounded-2xl border-0 shadow-2xl flex flex-col"
          style={{ width: '1000px', height: '700px', maxWidth: 'none', maxHeight: 'none' }}
        >
          <DialogHeader className="pb-4 flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-xl font-bold">
              <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center shadow-xl">
                <Smartphone className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-gray-900">Add New Device</div>
                <div className="text-xs font-normal text-gray-500 mt-0.5">Connect your iPhone to the automation system</div>
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="grid grid-cols-3 gap-4 flex-1 overflow-y-auto">
            {/* Left Column - Device Information */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl p-4 border border-gray-100">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-gray-100 rounded-md flex items-center justify-center">
                  <Smartphone className="w-3 h-3 text-gray-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">Device Information</h3>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="deviceName" className="text-xs font-semibold text-gray-700">
                    Device Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="deviceName"
                    type="text"
                    value={deviceName}
                    onChange={(e) => {
                      setDeviceName(e.target.value)
                      clearErrors()
                    }}
                    placeholder="e.g., iPhone 15 Pro - Device 1"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="udid" className="text-xs font-semibold text-gray-700">
                    Device UDID <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="udid"
                    type="text"
                    value={udid}
                    onChange={(e) => {
                      setUdid(e.target.value)
                      clearErrors()
                    }}
                    placeholder="e.g., 00008030-001A14E40C38802E"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 font-mono text-xs"
                    required
                  />
                  <p className="text-xs text-gray-500">
                    Find in Xcode → Window → Devices
                  </p>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="deviceType" className="text-xs font-semibold text-gray-700">
                    Device Type
                  </Label>
                  <Select value={jailbroken ? "jailbroken" : "non-jailbroken"} onValueChange={(value) => setJailbroken(value === "jailbroken")}>
                    <SelectTrigger className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs">
                      <SelectValue placeholder="Select device type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="non-jailbroken">Non-Jailbroken</SelectItem>
                      <SelectItem value="jailbroken">Jailbroken</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500">
                    Jailbroken devices support Crane containers
                  </p>
                </div>
              </div>
            </div>

            {/* Middle Column - Configuration */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50/50 rounded-xl p-4 border border-blue-100">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-blue-100 rounded-md flex items-center justify-center">
                  <RefreshCw className="w-3 h-3 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">Configuration</h3>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="ngrokToken" className="text-xs font-semibold text-gray-700">
                    ngrok Token (Optional)
                  </Label>
                  <Input
                    id="ngrokToken"
                    type="text"
                    value={ngrokToken}
                    onChange={(e) => setNgrokToken(e.target.value)}
                    placeholder="2abc123def456_your_token"
                    className="h-9 rounded-md border-gray-200 focus:border-blue-500 focus:ring-blue-500 text-xs"
                  />
                  <p className="text-xs text-gray-500">
                    Required for photo posting. Get from ngrok.com
                  </p>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="selectedModel" className="text-xs font-semibold text-gray-700">
                    Assigned Model
                  </Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger className="h-9 rounded-md border-gray-200 focus:border-blue-500 focus:ring-blue-500 text-xs">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {models.length > 0 ? (
                        models.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            <div className="flex items-center space-x-2">
                              {model.profilePhoto && (
                                <img src={model.profilePhoto} alt={model.name} className="w-4 h-4 rounded-full" />
                              )}
                              <User className="w-3 h-3" />
                              <span className="text-xs">{model.name}</span>
                            </div>
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="no-models" disabled>
                          No models available
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500">
                    Choose model for this device
                  </p>
                </div>
              </div>
            </div>

            {/* Right Column - Advanced Settings */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl p-4 border border-gray-100">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-gray-100 rounded-md flex items-center justify-center">
                  <RefreshCw className="w-3 h-3 text-gray-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">Advanced Settings</h3>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="appiumPort" className="text-xs font-semibold text-gray-700">
                    Appium Port
                  </Label>
                  <Input
                    id="appiumPort"
                    type="number"
                    value={appiumPort}
                    onChange={(e) => setAppiumPort(e.target.value)}
                    placeholder="4720"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                  />
                  <p className="text-xs text-gray-500">Port for Appium server</p>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="wdaPort" className="text-xs font-semibold text-gray-700">
                    WDA Port
                  </Label>
                  <Input
                    id="wdaPort"
                    type="number"
                    value={wdaPort}
                    onChange={(e) => setWdaPort(e.target.value)}
                    placeholder="8100"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                  />
                  <p className="text-xs text-gray-500">Port for WebDriverAgent</p>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="wdaBundleId" className="text-xs font-semibold text-gray-700">
                    WDA Bundle ID
                  </Label>
                  <Input
                    id="wdaBundleId"
                    type="text"
                    value={wdaBundleId}
                    onChange={(e) => setWdaBundleId(e.target.value)}
                    placeholder="com.device1.wd1"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                  />
                  <p className="text-xs text-gray-500">Bundle identifier for WebDriverAgent</p>
                </div>

              </div>
            </div>
          </div>

          {/* Error Messages */}
          {(deviceLimitError || generalError) && (
            <div className="mt-2 flex-shrink-0">
              {deviceLimitError && (
                <div className="bg-red-50 border border-red-200 rounded-md p-2 mb-1">
                  <div className="text-red-800 font-semibold text-xs">{deviceLimitError}</div>
                </div>
              )}
              {generalError && (
                <div className="bg-red-50 border border-red-200 rounded-md p-2">
                  <div className="text-red-800 font-semibold text-xs">{generalError}</div>
                </div>
              )}
            </div>
          )}

          {/* Compact Setup Instructions */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-md p-3 border border-blue-100 mt-2 flex-shrink-0">
            <h4 className="font-semibold text-gray-900 mb-2 text-xs">Quick Setup Guide</h4>
            <div className="grid grid-cols-3 gap-3 text-xs text-gray-700">
              <div className="flex items-center space-x-1">
                <div className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">1</div>
                <span>Enable Developer Mode</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">2</div>
                <span>Trust computer</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-4 h-4 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">3</div>
                <span>Auto-install WDA</span>
              </div>
            </div>
          </div>

          <DialogFooter className="pt-3 flex-shrink-0">
            <Button 
              type="button"
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="h-9 px-4 rounded-md border-2 border-gray-200 hover:border-gray-300 font-semibold text-xs"
              disabled={isLoadingDevice}
            >
              Cancel
            </Button>
            <Button 
              type="button"
              onClick={handleSubmit}
              disabled={isLoadingDevice || !deviceName.trim() || !udid.trim()}
              className="h-9 px-6 bg-black text-white hover:bg-gray-800 rounded-md font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 text-xs"
            >
              {isLoadingDevice ? (
                <div className="flex items-center space-x-1">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  <span>Adding...</span>
                </div>
              ) : (
                "Add Device"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Popup */}
      <SuccessPopup 
        isOpen={showSuccess} 
        onClose={() => setShowSuccess(false)} 
        message={successMessage} 
      />
    </>
  )
}