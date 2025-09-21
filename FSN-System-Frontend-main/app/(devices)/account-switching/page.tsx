"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AccountSwitcher } from "@/components/account-switching/account-switcher"
import { useDevices } from "@/lib/hooks/use-devices"
import { 
  Smartphone, 
  Instagram, 
  MessageSquare, 
  RefreshCw, 
  AlertCircle,
  Loader2
} from "lucide-react"

export default function AccountSwitchingPage() {
  const [selectedDevice, setSelectedDevice] = useState<string>("")
  const [selectedPlatform, setSelectedPlatform] = useState<'instagram' | 'threads'>('instagram')
  
  const { data: devices = [], isLoading: devicesLoading, error: devicesError, refetch } = useDevices()
  
  const selectedDeviceData = devices.find(device => device.udid === selectedDevice)

  if (devicesLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading devices...</p>
        </div>
      </div>
    )
  }

  if (devicesError) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="w-4 h-4" />
          <AlertDescription>
            Failed to load devices: {devicesError.message}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (devices.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Smartphone className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No devices found</h3>
          <p className="text-muted-foreground mb-4">
            Connect a device to test account switching
          </p>
          <Button onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Account Switching</h1>
          <p className="text-muted-foreground">
            Switch between accounts on Instagram and Threads
          </p>
        </div>
        <Button onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh Devices
        </Button>
      </div>

      {/* Device Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Device & Platform</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Device Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Device</label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {devices.map((device) => (
                <div
                  key={device.udid}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDevice === device.udid
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedDevice(device.udid)}
                >
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{device.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{device.udid}</div>
                    </div>
                    <Badge variant={device.status === 'online' ? 'default' : 'secondary'}>
                      {device.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Platform Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Platform</label>
            <div className="flex gap-2">
              <Button
                variant={selectedPlatform === 'instagram' ? 'default' : 'outline'}
                onClick={() => setSelectedPlatform('instagram')}
                className="flex-1"
              >
                <Instagram className="w-4 h-4 mr-2" />
                Instagram
              </Button>
              <Button
                variant={selectedPlatform === 'threads' ? 'default' : 'outline'}
                onClick={() => setSelectedPlatform('threads')}
                className="flex-1"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Threads
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Account Switcher */}
      {selectedDevice && selectedDeviceData && (
        <AccountSwitcher 
          device={selectedDeviceData} 
          platform={selectedPlatform} 
        />
      )}

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>How to Use</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <h4 className="font-medium">Step 1: Launch App</h4>
            <p className="text-sm text-muted-foreground">
              Click "Launch App" to open {selectedPlatform} and navigate to the profile tab
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">Step 2: Open Switcher</h4>
            <p className="text-sm text-muted-foreground">
              Click "Open Switcher" to open the account switching dropdown
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">Step 3: Select Account</h4>
            <p className="text-sm text-muted-foreground">
              Choose an account from the available list and click "Switch Account"
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">Complete Flow</h4>
            <p className="text-sm text-muted-foreground">
              Or use "Complete Flow" to do all steps automatically
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
