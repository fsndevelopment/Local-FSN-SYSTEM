"use client"

import { HeroCard } from "@/components/hero-card"
import { StatusBadge } from "@/components/status-badge"
import { LogViewer } from "@/components/log-viewer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Smartphone, Users, AlertTriangle, ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { DeviceWithTemplate, Template } from "@/lib/types"
import { useState, useEffect } from "react"
import { calculateDeviceCapacity } from "@/lib/utils/capacity-calculator"
import { useDevice } from "@/lib/hooks/use-devices"
import { useTemplates } from "@/lib/hooks/use-templates"
import { useAccounts } from "@/lib/hooks/use-accounts"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"

// Device detail page component

export default function DeviceDetailPage({ params }: { params: { id: string } }) {
  const deviceId = parseInt(params.id)
  
  // Fetch real data from APIs
  const { data: device, isLoading: deviceLoading, error: deviceError } = useDevice(deviceId)
  const { data: templatesData, isLoading: templatesLoading } = useTemplates()
  const { data: accounts, isLoading: accountsLoading } = useAccounts()
  
  // Extract templates array from the query result
  const templates = templatesData?.data?.items || []
  const [warmupTemplates, setWarmupTemplates] = useState<{ id: string, name: string }[]>([])

  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("")
  const [selectedWarmupTemplateId, setSelectedWarmupTemplateId] = useState<string>("")
  const [deviceCapacity, setDeviceCapacity] = useState("safe")

  // Set initial template when device loads
  useEffect(() => {
    if (device?.template_id) {
      setSelectedTemplateId(device.template_id.toString())
    }
    // Load warmup assignment from storage
    const warmupAssign = licenseAwareStorageService.getDeviceWarmupTemplates()[String(deviceId)]
    if (warmupAssign) setSelectedWarmupTemplateId(String(warmupAssign))
    // Load warmup templates list from storage
    licenseAwareStorageService.getWarmupTemplates().then(list => {
      setWarmupTemplates(list.map(t => ({ id: t.id, name: t.name })))
    }).catch(() => {})
  }, [device])

  // Update device capacity when template changes
  useEffect(() => {
    if (device && templates) {
      const selectedTemplate = templates.find(t => t.id.toString() === selectedTemplateId)
      if (selectedTemplate) {
        const updatedDevice = {
          ...device,
          templateId: selectedTemplateId,
          template: selectedTemplate
        }
        const capacity = calculateDeviceCapacity(updatedDevice, device.assignedAccounts || [])
        setDeviceCapacity(capacity.status)
      }
    }
  }, [selectedTemplateId, device, templates])

  const handleTemplateChange = (templateId: string) => {
    if (templateId === "none") {
      setSelectedTemplateId("")
    } else {
      setSelectedTemplateId(templateId)
    }
    // TODO: Make API call to update device template
    console.log('Template changed to:', templateId)
  }

  const handleWarmupTemplateChange = (templateId: string) => {
    if (templateId === "none") {
      setSelectedWarmupTemplateId("")
      licenseAwareStorageService.removeWarmupTemplateFromDevice(String(deviceId))
    } else {
      setSelectedWarmupTemplateId(templateId)
      licenseAwareStorageService.assignWarmupTemplateToDevice(String(deviceId), templateId)
    }
    console.log('Warmup Template changed to:', templateId)
  }

  const selectedTemplate = templates?.find(t => t.id.toString() === selectedTemplateId)

  // Loading state
  if (deviceLoading || templatesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading device and templates...</span>
      </div>
    )
  }

  // Error state
  if (deviceError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Error Loading Device</h3>
          <p className="text-muted-foreground mb-4">
            {deviceError.detail || 'Failed to load device information'}
          </p>
          <Link href="/devices">
            <Button variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Devices
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  // No device found
  if (!device) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Smartphone className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Device Not Found</h3>
          <p className="text-muted-foreground mb-4">The requested device could not be found.</p>
          <Link href="/devices">
            <Button variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Devices
            </Button>
          </Link>
        </div>
      </div>
    )
  }


  return (
    <div className="space-y-6">
      <HeroCard title={device.name} subtitle={`UDID: ${device.udid.slice(0, 16)}...`}>
        <div className="flex space-x-2">
          <Link href="/devices">
            <Button variant="outline" className="rounded-full px-4 border-border bg-transparent">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Devices
            </Button>
          </Link>
        </div>
      </HeroCard>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Device info and accounts */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-2xl shadow p-6">
            <h3 className="font-semibold mb-4">Device Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Model</div>
                <div className="font-medium">{device.model || "Unknown"}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Appium Port</div>
                <div className="font-medium font-mono">{device.appium_port}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">WDA Port</div>
                <div className="font-medium font-mono">{device.wda_port}</div>
              </div>
            </div>
          </div>

          {/* Template Assignment & Capacity */}
          <div className="bg-card rounded-2xl shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Template</h3>
            </div>
            
            <div className="space-y-4">
              {/* Current Template */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">
                    {selectedTemplate ? selectedTemplate.name : "No Template Assigned"}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {selectedTemplate ? `${selectedTemplate.photos_per_day || 0} photos, ${selectedTemplate.text_posts_per_day || 0} text posts, ${selectedTemplate.likes_per_day || 0} likes, ${selectedTemplate.follows_per_day || 0} follows per day` : "Assign a template to set daily limits"}
                  </div>
                </div>
                <Select value={selectedTemplateId || "none"} onValueChange={handleTemplateChange}>
                  <SelectTrigger className="w-40 h-8" data-template-select>
                    <SelectValue placeholder="Select template" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      <div className="flex items-center space-x-2">
                        <span className="text-muted-foreground">No Template</span>
                      </div>
                    </SelectItem>
                    {templates?.map((template) => (
                      <SelectItem key={template.id} value={template.id.toString()}>
                        <div className="flex items-center justify-between w-full">
                          <span>{template.name}</span>
                          <span className="text-xs text-muted-foreground ml-2">
                            {(template.photos_per_day || 0) + (template.text_posts_per_day || 0) + (template.likes_per_day || 0) + (template.follows_per_day || 0)} actions/day
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Warmup Template Assignment */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">
                    {selectedWarmupTemplateId ? (warmupTemplates.find(t => t.id === selectedWarmupTemplateId)?.name || 'Warmup Template') : "No Warmup Template Assigned"}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Select a warmup template for this device
                  </div>
                </div>
                <Select value={selectedWarmupTemplateId || "none"} onValueChange={handleWarmupTemplateChange}>
                  <SelectTrigger className="w-40 h-8" data-warmup-template-select>
                    <SelectValue placeholder="Select warmup" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      <div className="flex items-center space-x-2">
                        <span className="text-muted-foreground">No Warmup</span>
                      </div>
                    </SelectItem>
                    {warmupTemplates.map((t) => (
                      <SelectItem key={t.id} value={t.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>{t.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Capacity Indicator */}
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium">Device Capacity</span>
                  <Badge variant="outline" className="bg-gray-100 text-gray-800 border-gray-200">
                    <span className="text-sm font-medium capitalize">{deviceCapacity}</span>
                  </Badge>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Assigned Accounts</div>
                    <div className="font-medium">{device.assignedAccounts?.length || 0}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Daily Actions</div>
                    <div className="font-medium">
                      {selectedTemplate ? 
                        (selectedTemplate.photos_per_day || 0) + (selectedTemplate.text_posts_per_day || 0) + 
                        (selectedTemplate.likes_per_day || 0) + (selectedTemplate.follows_per_day || 0) : 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Scrolling Time</div>
                    <div className="font-medium">
                      {selectedTemplate ? `${selectedTemplate.scrolling_time_minutes || 0} min` : "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-2xl shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Assigned Accounts</h3>
            </div>

            <div className="space-y-3">
              {device.assignedAccounts && device.assignedAccounts.length > 0 ? (
                device.assignedAccounts.map((account) => (
                  <div
                    key={account.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-sm">{account.username}</div>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge variant="outline" className="text-xs border-gray-300">
                          {account.role || "USER"}
                        </Badge>
                        <Badge variant="outline" className="text-xs border-gray-300">
                          {account.status === "active" ? "Active" : "Warming up"}
                        </Badge>
                      </div>
                    </div>

                    <Link href={`/accounts/${account.id}`}>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 bg-gray-800 text-white hover:bg-gray-900 border-gray-800"
                      >
                        Open
                      </Button>
                    </Link>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No accounts assigned to this device</p>
                  <p className="text-xs mt-1">Assign accounts from the Accounts tab</p>
                </div>
              )}
            </div>
          </div>

          <LogViewer deviceId={deviceId} />
        </div>

        {/* Right column - Quick stats */}
        <div className="space-y-6">
          <div className="bg-card rounded-2xl shadow p-6">
            <h3 className="font-semibold mb-4">Quick Stats</h3>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-muted-foreground">Uptime</div>
                <div className="text-lg font-semibold">-</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Actions Today</div>
                <div className="text-lg font-semibold">-</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Success Rate</div>
                <div className="text-lg font-semibold">-</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Last Error</div>
                <div className="text-sm">-</div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}