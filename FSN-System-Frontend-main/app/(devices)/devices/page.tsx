"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { DataListCard } from "@/components/data-list-card"
import { StatusBadge } from "@/components/status-badge"
import { HeroCard } from "@/components/hero-card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Smartphone, Plus, RefreshCw, AlertTriangle, LayoutTemplate, Info, CheckCircle, AlertTriangle as AlertTriangleIcon, User, Trash2 } from "lucide-react"
import { useDevices, useDeviceStats, useDeleteDevice } from "@/lib/hooks/use-devices"
import { formatDistanceToNow } from "date-fns"
import type { Device } from "@/lib/api/devices"
import { licenseAwareStorageService, LocalDevice, LocalWarmupTemplate } from "@/lib/services/license-aware-storage-service"
import { Template, DeviceWithTemplate } from "@/lib/types"
import { calculateDeviceCapacity } from "@/lib/utils/capacity-calculator"
import { usePlatform } from "@/lib/platform"
import { LicenseBlocker } from "@/components/license-blocker"
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { PlatformHeader } from "@/components/platform-header"
import { AddDeviceDialog } from "@/components/add-device-dialog"
import { FeasibilityIndicator } from "@/components/feasibility-indicator"

// Model interface
interface Model {
  id: string
  name: string
  profilePhoto?: string
  created_at: string
  updated_at: string
}


export default function DevicesPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [mockDevices, setMockDevices] = useState<Device[]>([])
  const [deviceTemplates, setDeviceTemplates] = useState<Record<string, string>>({})
  const [availableTemplates, setAvailableTemplates] = useState<Template[]>([])
  const [availableWarmupTemplates, setAvailableWarmupTemplates] = useState<LocalWarmupTemplate[]>([])
  const [deviceWarmupTemplates, setDeviceWarmupTemplates] = useState<Record<string, string>>({})
  const [devicePhases, setDevicePhases] = useState<Record<string, 'posting' | 'warmup'>>({})
  const [deviceWarmupDays, setDeviceWarmupDays] = useState<Record<string, number>>({})
  const [models, setModels] = useState<Model[]>([])
  const [accounts, setAccounts] = useState<any[]>([])
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [deletedDevices, setDeletedDevices] = useState<Set<string>>(new Set())
  const [isAddDeviceDialogOpen, setIsAddDeviceDialogOpen] = useState(false)
  const processedParams = useRef<Set<string>>(new Set())
  const [platform] = usePlatform()
  
  // Always fetch all devices, then filter on frontend
  const { data: allDevicesResponse, isLoading, error, refetch } = useDevices()
  
  // Handle both array format and paginated response format
  const allDevices = Array.isArray(allDevicesResponse) 
    ? allDevicesResponse 
    : allDevicesResponse?.devices || []
  
  // Debug logging
  console.log('🔍 DEVICE DEBUG - allDevicesResponse:', allDevicesResponse)
  console.log('🔍 DEVICE DEBUG - allDevices:', allDevices)
  console.log('🔍 DEVICE DEBUG - isLoading:', isLoading)
  console.log('🔍 DEVICE DEBUG - error:', error)
  
  // Debug localStorage devices
  console.log('🔍 DEVICE DEBUG - localStorage devices:', licenseAwareStorageService.getDevices())
  console.log('🔍 DEVICE DEBUG - mockDevices:', mockDevices)
  
  // React Query mutation for device deletion
  const deleteDeviceMutation = useDeleteDevice()
  
  // Load templates and warmup templates from license-aware storage
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        // Load posting templates
        const savedTemplates = await licenseAwareStorageService.getTemplates()
        // Filter templates by current platform (show all if platform is 'all')
        const filteredTemplates = platform === 'all' 
          ? savedTemplates 
          : savedTemplates.filter((t: Template) => t.platform === platform)
        setAvailableTemplates(filteredTemplates)
        
        // Load warmup templates
        const savedWarmupTemplates = await licenseAwareStorageService.getWarmupTemplates()
        console.log('🔥 DEVICES DEBUG - Loaded warmup templates:', savedWarmupTemplates)
        // Filter warmup templates by current platform
        const filteredWarmupTemplates = savedWarmupTemplates.filter((t: LocalWarmupTemplate) => t.platform === platform)
        console.log('🔥 DEVICES DEBUG - Filtered warmup templates for platform:', platform, filteredWarmupTemplates)
        setAvailableWarmupTemplates(filteredWarmupTemplates)
        
      } catch (error) {
        console.error('Failed to load templates:', error)
        setAvailableTemplates([])
        setAvailableWarmupTemplates([])
      }
    }
    
    loadTemplates()
  }, [platform])

  // Load device template assignments and accounts from license-aware storage
  useEffect(() => {
    const loadDeviceData = async () => {
      try {
        const savedDeviceTemplates = licenseAwareStorageService.getDeviceTemplates()
        const savedDeviceWarmupTemplates = (licenseAwareStorageService as any).getItem?.('deviceWarmupTemplates') || {}
        const savedDevicePhases = (licenseAwareStorageService as any).getItem?.('devicePhases') || {}
        const savedDeviceWarmupDays = (licenseAwareStorageService as any).getItem?.('deviceWarmupDays') || {}
        const savedAccounts = await licenseAwareStorageService.getAccounts()
        
        setDeviceTemplates(savedDeviceTemplates || {})
        setDeviceWarmupTemplates(savedDeviceWarmupTemplates || {})
        setDevicePhases(savedDevicePhases || {})
        setDeviceWarmupDays(savedDeviceWarmupDays || {})
        setAccounts(savedAccounts || [])
      } catch (error) {
        console.error('Failed to load device data:', error)
        setAccounts([])
      }
    }
    
    loadDeviceData()
  }, [])

  // Load saved devices from license-aware storage service
  useEffect(() => {
    const savedDevices = licenseAwareStorageService.getDevices()
    
    // Clean up duplicate devices - if we have backend devices, don't show mock devices with same UDID
    if (allDevices && allDevices.length > 0) {
      const backendUdids = new Set(allDevices.map((device: any) => device.udid))
      const filteredMockDevices = savedDevices.filter((device: any) => !backendUdids.has(device.udid))
      setMockDevices(filteredMockDevices)
      
      // If we filtered out devices, update license-aware storage
      if (filteredMockDevices.length !== savedDevices.length) {
        console.log('🧹 CLEANUP - Removed duplicate mock devices, keeping only unique ones')
        licenseAwareStorageService.saveDevices(filteredMockDevices)
      }
    } else {
      setMockDevices(savedDevices)
    }
  }, [allDevices])

  // Load deleted devices from localStorage
  useEffect(() => {
    const savedDeletedDevices = localStorage.getItem('deletedDevices')
    if (savedDeletedDevices) {
      try {
        const deletedArray = JSON.parse(savedDeletedDevices)
        // Safety check: if all devices are marked as deleted, clear the localStorage
        if (deletedArray.length > 0) {
          console.log('🔍 DEVICE DEBUG - Loaded deleted devices from localStorage:', deletedArray)
          // Check if this would filter out all devices - if so, clear it
          const currentDevices = allDevices || []
          const wouldFilterAll = currentDevices.length > 0 && currentDevices.every((device: any) => 
            deletedArray.includes(device.id.toString())
          )
          if (wouldFilterAll) {
            console.log('🚨 SAFETY CHECK - All devices would be filtered out, clearing deletedDevices')
            localStorage.removeItem('deletedDevices')
            setDeletedDevices(new Set())
            return
          }
        }
        setDeletedDevices(new Set(deletedArray))
      } catch (error) {
        console.error('Failed to parse deleted devices:', error)
        // Clear corrupted data
        localStorage.removeItem('deletedDevices')
        setDeletedDevices(new Set())
      }
    } else {
      console.log('🔍 DEVICE DEBUG - No deleted devices in localStorage')
    }
  }, [allDevices])

  // Load models from license-aware storage
  useEffect(() => {
    const loadModels = async () => {
      try {
        const savedModels = await licenseAwareStorageService.getModels()
        // Convert LocalModel[] to Model[] by adding missing properties
        const modelsWithTimestamps = savedModels.map(model => ({
          ...model,
          created_at: model.createdAt || new Date().toISOString(),
          updated_at: model.updatedAt || new Date().toISOString()
        }))
        setModels(modelsWithTimestamps)
      } catch (error) {
        console.error('Failed to load models:', error)
        setModels([])
      }
    }
    
    loadModels()
  }, [])

  const handleTemplateChange = (deviceId: string, templateId: string) => {
    if (templateId === "none") {
      licenseAwareStorageService.removeTemplateFromDevice(deviceId)
    } else {
      licenseAwareStorageService.assignTemplateToDevice(deviceId, templateId)
    }
    
    // Update local state
    const newDeviceTemplates = licenseAwareStorageService.getDeviceTemplates()
    setDeviceTemplates(newDeviceTemplates)
  }

  const handleWarmupTemplateChange = (deviceId: string, warmupTemplateId: string) => {
    const newDeviceWarmupTemplates = { ...deviceWarmupTemplates }
    
    if (warmupTemplateId === "none") {
      delete newDeviceWarmupTemplates[deviceId]
    } else {
      newDeviceWarmupTemplates[deviceId] = warmupTemplateId
    }
    
    // Save to storage
    ;(licenseAwareStorageService as any).setItem?.('deviceWarmupTemplates', newDeviceWarmupTemplates)
    setDeviceWarmupTemplates(newDeviceWarmupTemplates)
  }

  const handlePhaseChange = (deviceId: string, phase: 'posting' | 'warmup') => {
    const newDevicePhases = { ...devicePhases }
    newDevicePhases[deviceId] = phase
    
    // Save to storage
    ;(licenseAwareStorageService as any).setItem?.('devicePhases', newDevicePhases)
    setDevicePhases(newDevicePhases)
  }

  const handleWarmupDayChange = (deviceId: string, day: number) => {
    const newDeviceWarmupDays = { ...deviceWarmupDays }
    newDeviceWarmupDays[deviceId] = day
    
    // Save to storage
    ;(licenseAwareStorageService as any).setItem?.('deviceWarmupDays', newDeviceWarmupDays)
    setDeviceWarmupDays(newDeviceWarmupDays)
  }

  const handleDeleteDevice = async (deviceId: string) => {
    console.log('Deleting device with ID:', deviceId)
    
    try {
      // Check if it's a mock device (from local storage)
      const isMockDevice = mockDevices.some(device => device.id.toString() === deviceId)
      
      if (isMockDevice) {
        // Delete from license-aware storage service
        licenseAwareStorageService.deleteDevice(parseInt(deviceId))
        
        // Update local state
        setMockDevices(prev => {
          const updatedDevices = prev.filter(device => device.id.toString() !== deviceId)
          console.log('Updated mock devices after deletion:', updatedDevices)
          return updatedDevices
        })
      } else {
        // For backend devices, call the API to delete from database
        console.log('Deleting backend device via API:', deviceId)
        
        // Use the deviceId directly as a string, not parseInt
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices/${deviceId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        })
        
        if (!response.ok) {
          throw new Error(`Failed to delete device: ${response.statusText}`)
        }
        
        console.log('Backend device deleted successfully:', deviceId)
      }
      
      // Clear delete confirmation
      setDeleteConfirm(null)
    } catch (error) {
      console.error('Failed to delete device:', error)
      // Keep confirmation dialog open on error
    }
  }

  const confirmDeleteDevice = (deviceId: string) => {
    console.log('Confirming delete for device ID:', deviceId)
    setDeleteConfirm(deviceId)
  }

  const cancelDeleteDevice = () => {
    setDeleteConfirm(null)
  }

  const getCapacityStatus = (device: Device): "safe" | "warning" | "overloaded" => {
    const templateId = deviceTemplates[device.id.toString()]
    if (!templateId) return "safe"
    
    const template = availableTemplates.find(t => t.id === templateId)
    if (!template) return "safe"
    
    const deviceWithTemplate: DeviceWithTemplate = {
      ...device,
      templateId,
      template,
      capacityStatus: "safe",
      assignedAccountsCount: 0 // Mock count
    }
    
    const capacity = calculateDeviceCapacity(deviceWithTemplate, [])
    return capacity.status
  }

  const getCapacityIcon = (status: "safe" | "warning" | "overloaded") => {
    switch (status) {
      case "safe":
        return <CheckCircle className="w-4 h-4 text-gray-600" />
      case "warning":
        return <AlertTriangleIcon className="w-4 h-4 text-gray-600" />
      case "overloaded":
        return <AlertTriangleIcon className="w-4 h-4 text-gray-600" />
    }
  }

  const getCapacityColor = (status: "safe" | "warning" | "overloaded") => {
    switch (status) {
      case "safe":
        return "bg-gray-100 text-gray-800 border-gray-200"
      case "warning":
        return "bg-gray-100 text-gray-800 border-gray-200"
      case "overloaded":
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }
  
  // Check for mock device addition from URL params
  useEffect(() => {
    const deviceName = searchParams.get('deviceName')
    const udid = searchParams.get('udid')
    const appiumPort = searchParams.get('appiumPort')
    const wdaPort = searchParams.get('wdaPort')
    
    if (deviceName && udid) {
      // Create a unique key for this device addition
      const deviceKey = `${deviceName}-${udid}`
      
      // Check if we've already processed this device addition
      if (!processedParams.current.has(deviceKey)) {
        // Mark as processed
        processedParams.current.add(deviceKey)
        
        // Create a mock device
        const newMockDevice: Device = {
          id: Date.now(), // Use timestamp as unique ID
          name: deviceName,
          udid: udid,
          ios_version: '17.2.1',
          model: 'iPhone 15 Pro',
          appium_port: parseInt(appiumPort || '4720'),
          wda_port: parseInt(wdaPort || '8100'),
          mjpeg_port: Math.floor(9100 + Math.random() * 1000), // Keep MJPEG random
          wda_bundle_id: undefined,
          jailbroken: false,
          status: 'active',
          last_seen: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
        
        // Add to state and save to license-aware storage
        setMockDevices(prev => {
          const updatedDevices = [...prev, newMockDevice]
          // Convert Device[] to LocalDevice[] for storage
          const localDevices = updatedDevices.map(device => ({
            ...device,
            ios_version: device.ios_version || 'Unknown',
            model: device.model || 'Unknown',
            updated_at: device.updated_at || new Date().toISOString()
          }))
          licenseAwareStorageService.saveDevices(localDevices)
          return updatedDevices
        })
      }
      
      // Clear URL params
      const newUrl = new URL(window.location.href)
      newUrl.searchParams.delete('deviceName')
      newUrl.searchParams.delete('udid')
      newUrl.searchParams.delete('appiumPort')
      newUrl.searchParams.delete('wdaPort')
      window.history.replaceState({}, '', newUrl.toString())
    }
  }, [searchParams]) // Only depend on searchParams
  
  // Combine real devices with mock devices, ensuring unique IDs
  const combinedDevices = [...(allDevices || []), ...mockDevices].reduce((acc: Device[], device: Device) => {
    // Use device ID as key to prevent duplicates
    const key = device.id.toString()
    if (!acc.find((d: Device) => d.id.toString() === key)) {
      acc.push(device)
    }
    return acc
  }, [] as Device[])
  
  // Debug logging
  console.log('🔍 DEVICE DEBUG - combinedDevices:', combinedDevices)
  console.log('🔍 DEVICE DEBUG - allDevices length:', allDevices?.length || 0)
  console.log('🔍 DEVICE DEBUG - mockDevices length:', mockDevices.length)
  
  // Filter devices - only exclude deleted devices
  const devices = combinedDevices?.filter((device: Device) => {
    // Exclude deleted devices
    const isDeleted = deletedDevices.has(device.id.toString())
    console.log('🔍 DEVICE FILTER DEBUG - Device ID:', device.id, 'isDeleted:', isDeleted)
    return !isDeleted
  })
  
  // Debug logging
  console.log('🔍 DEVICE DEBUG - deletedDevices Set:', Array.from(deletedDevices))
  console.log('🔍 DEVICE DEBUG - devices after filtering:', devices)
  const { stats, isLoading: statsLoading } = useDeviceStats()

  // Calculate total devices, excluding deleted devices
  const totalDevices = combinedDevices?.filter((device: Device) => !deletedDevices.has(device.id.toString())).length || 0

  // Transform device data for DataListCard
  const deviceItems = devices?.map((device: Device | LocalDevice) => {
    // Use the actual device name instead of transforming it
    const deviceName = device.name
    console.log('🔍 DEVICE NAME DEBUG - Device ID:', device.id, 'Name:', deviceName, 'Full device:', device)
    const displayStatus = device.status
    
    const selectedTemplateId = deviceTemplates[device.id.toString()]
    const selectedTemplate = availableTemplates.find(t => t.id === selectedTemplateId)
    const capacityStatus = getCapacityStatus(device)
    
    // Check if this is a local device with model information
    const isLocalDevice = 'model' in device && typeof device.model === 'string'
    const assignedModel = isLocalDevice ? models.find(m => m.name === device.model) : null
    
    return {
      id: device.id.toString(),
      title: deviceName,
      subtitle: `UDID: ${device.udid.substring(0, 8)}...${device.udid.substring(-6)}`,
      meta: [
        `Appium: ${device.appium_port}`,
        `WDA: ${device.wda_port}`,
        isLocalDevice && device.model && device.model !== 'No Model Selected' ? `Model: ${device.model}` : null,
        device.last_seen ? `Last seen: ${formatDistanceToNow(new Date(device.last_seen), { addSuffix: true })}` : 'Last seen: Never'
      ].filter(Boolean).join(" • "),
      badge: (
        <div className="flex items-center space-x-2">
          {/* Capacity Indicator */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Badge className={`border ${getCapacityColor(capacityStatus)}`}>
                  {getCapacityIcon(capacityStatus)}
                  <span className="ml-1 text-xs">
                    {capacityStatus.charAt(0).toUpperCase() + capacityStatus.slice(1)}
                  </span>
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs">
                  {capacityStatus === "safe" && "Device is operating within safe limits. Recommended to stay in green zone to avoid complications."}
                  {capacityStatus === "warning" && "Device is approaching capacity limits. Consider reducing assigned accounts or template intensity."}
                  {capacityStatus === "overloaded" && "Device is overloaded. Too many accounts or actions assigned. Reduce load immediately to prevent issues."}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      ),
      action: {
        label: "View",
        onClick: () => router.push(`/devices/${device.id}`)
      },
      actions: [
        {
          label: "View",
          onClick: () => router.push(`/devices/${device.id}`),
          variant: "default" as const
        },
        {
          label: "",
          onClick: () => confirmDeleteDevice(device.id.toString()),
          variant: "destructive" as const,
          icon: <Trash2 className="w-4 h-4" />
        }
      ],
      // Add template selection as additional content
      additionalContent: (
        <div className="mt-3 space-y-2">
          {/* Assigned Model Info */}
          {assignedModel && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span>Assigned Model: <span className="font-medium text-foreground">{assignedModel.name}</span></span>
            </div>
          )}
          
          {/* Compact Configuration */}
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Templates column */}
              <div className="space-y-2">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Templates</div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Posting Template</span>
                  <Select 
                    value={selectedTemplateId || "none"} 
                    onValueChange={(value) => handleTemplateChange(device.id.toString(), value)}
                  >
                    <SelectTrigger className="w-40 h-8 text-xs">
                      <SelectValue placeholder="Select posting" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Template</SelectItem>
                      {availableTemplates.map((template) => (
                        <SelectItem key={template.id} value={template.id}>
                          <div className="flex items-center justify-between w-full">
                            <span>{template.name}</span>
                            <span className="text-xs text-muted-foreground ml-2">
                              {template.photosPostsPerDay + template.textPostsPerDay + template.likesPerDay + template.followsPerDay} actions/day
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {selectedTemplateId && selectedTemplateId !== "none" && (
                  <div className="p-2 bg-white rounded-lg border">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-700">Schedule Feasibility</span>
                      <FeasibilityIndicator
                        deviceId={device.id.toString()}
                        accounts={accounts.filter(account => account.device === device.id.toString())}
                        template={availableTemplates.find(t => t.id === selectedTemplateId)}
                        showDetails={true}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Warmup column */}
              <div className="space-y-2">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Warmup</div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Warmup Template</span>
                  <Select 
                    value={deviceWarmupTemplates[device.id.toString()] || "none"} 
                    onValueChange={(value) => handleWarmupTemplateChange(device.id.toString(), value)}
                  >
                    <SelectTrigger className="w-40 h-8 text-xs">
                      <SelectValue placeholder="Select warmup" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Warmup</SelectItem>
                      {availableWarmupTemplates.map((template) => (
                        <SelectItem key={template.id} value={template.id}>
                          <div className="flex items-center justify-between w-full">
                            <span>{template.name}</span>
                            <span className="text-xs text-muted-foreground ml-2">
                              {template.days?.length || 0} days
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {deviceWarmupTemplates[device.id.toString()] && deviceWarmupTemplates[device.id.toString()] !== "none" && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Current Day</span>
                    <Select 
                      value={deviceWarmupDays[device.id.toString()]?.toString() || "1"} 
                      onValueChange={(value) => handleWarmupDayChange(device.id.toString(), parseInt(value))}
                    >
                      <SelectTrigger className="w-24 h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {(() => {
                          const selectedWarmupTemplateId = deviceWarmupTemplates[device.id.toString()]
                          const selectedWarmupTemplate = availableWarmupTemplates.find(t => t.id === selectedWarmupTemplateId)
                          const dayCount = selectedWarmupTemplate?.days?.length || 1
                          return Array.from({ length: dayCount }, (_, i) => (
                            <SelectItem key={i + 1} value={(i + 1).toString()}>
                              Day {i + 1}
                            </SelectItem>
                          ))
                        })()}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )
    }
  }) || []

  const handleRefresh = () => {
    refetch()
  }

  if (error) {
    return (
      <LicenseBlocker action="access device management">
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6">
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Failed to load devices: {(error as any)?.detail || 'Unknown error'}
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleRefresh}
                    className="ml-2"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                  </Button>
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </div>
      </LicenseBlocker>
    )
  }

  return (
    <LicenseBlocker action="access device management">
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
        {/* Main Header Section - Platform Colors */}
        <PlatformHeader>
          <div className="absolute inset-0 opacity-10 bg-[length:40px_40px] bg-[image:url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')]"></div>
          
          <div className="relative px-6 py-12">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-center justify-between">
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-2xl">
                      <Smartphone className="w-6 h-6 text-black" />
                    </div>
                    <div>
                      <h1 className="text-4xl font-bold text-white tracking-tight">Device Management</h1>
                      <p className="text-gray-300 text-lg mt-1">Monitor and control your Appium device farm</p>
                    </div>
                  </div>
                  
                  {/* Live Status Indicator */}
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                      <div className="relative">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                        <div className="absolute inset-0 w-2 h-2 bg-blue-400 rounded-full animate-ping opacity-75"></div>
                      </div>
                      <span className="text-white text-sm font-medium">Devices Active</span>
                    </div>
                    
                    <div className="text-white/60 text-sm">
                      Last updated: {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                  <div className="flex items-center space-x-4">
                    <Button 
                      variant="outline"
                      onClick={handleRefresh}
                      disabled={isLoading}
                      className="bg-white/10 text-white border-white/20 hover:bg-white/20 rounded-2xl px-4 py-2"
                    >
                      <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                    <Button 
                      onClick={() => setIsAddDeviceDialogOpen(true)}
                      className="bg-white text-black hover:bg-gray-100 font-semibold px-6 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] border-0"
                    >
                      <Plus className="w-5 h-5 mr-2" />
                      Add Device
                    </Button>
                    <Button 
                      onClick={() => router.push('/devices/connect')}
                      className="bg-white/10 text-white border-white/20 hover:bg-white/20 rounded-2xl px-4 py-2"
                    >
                      <Smartphone className="w-4 h-4 mr-2" />
                      Connect Mac Agent
                    </Button>
                  </div>
                </div>
              </div>
              
              {/* Search Bar and Platform Switcher - Integrated into header */}
              <div className="mt-8">
                <div className="flex items-center justify-between">
                  {/* Search */}
                  <div className="flex-1 max-w-md">
                    <GlobalSearchBar placeholder="Search devices..." />
                  </div>

                  {/* Right side */}
                  <div className="flex items-center space-x-4">
                    <PlatformSwitch />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </PlatformHeader>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 gap-8">
          {/* Device List */}
          <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6">
              <DataListCard
                title={`Connected Devices - Total: ${isLoading ? '...' : totalDevices}`}
                items={deviceItems}
                isLoading={isLoading}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-2xl shadow-lg p-6 w-full max-w-md">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Delete Device</h3>
                <p className="text-sm text-muted-foreground">This action cannot be undone</p>
              </div>
            </div>
            
            <p className="text-sm text-muted-foreground mb-6">
              Are you sure you want to delete this device? All associated data will be permanently removed.
            </p>
            
            <div className="flex space-x-3">
              <Button
                variant="destructive"
                onClick={() => handleDeleteDevice(deleteConfirm!)}
                className="flex-1"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Device
              </Button>
              <Button
                variant="outline"
                onClick={cancelDeleteDevice}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Add Device Dialog */}
      <AddDeviceDialog 
        open={isAddDeviceDialogOpen}
        onOpenChange={setIsAddDeviceDialogOpen}
        onDeviceAdded={() => {
          refetch() // Refresh the devices list
        }}
      />
      </LicenseBlocker>
    )
  }