"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileText, AlertTriangle, CheckCircle, XCircle, Clock, RefreshCw, Download, Calendar as CalendarIcon, Smartphone } from "lucide-react"
import { LicenseBlocker } from "@/components/license-blocker"
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { PlatformHeader } from "@/components/platform-header"
import { CalendarPopup } from "@/components/calendar-popup"
import { useDevices } from "@/lib/hooks/use-devices"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"

// Log entry interface
interface LogEntry {
  id: string
  timestamp: string
  level: "error" | "warning" | "success" | "info"
  source: string
  message: string
  details: string
  device_id?: string
  device_name?: string
}

export default function LogsPage() {
  // State management
  const [selectedDevice, setSelectedDevice] = useState<string>("all")
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date())
  const [isCalendarOpen, setIsCalendarOpen] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Load devices
  const { data: apiDevicesResponse } = useDevices()
  const [allDevices, setAllDevices] = useState<any[]>([])

  // Load devices from both API and local storage
  useEffect(() => {
    const loadDevices = () => {
      try {
        const savedDevices = licenseAwareStorageService.getDevices()
        const apiDevices = Array.isArray(apiDevicesResponse) 
          ? apiDevicesResponse 
          : apiDevicesResponse?.devices || []
        
        const combined = [...apiDevices, ...savedDevices]
        const unique = combined.filter((device, index, self) => 
          index === self.findIndex(d => d.id === device.id)
        )
        
        setAllDevices(unique)
      } catch (error) {
        console.error('Failed to load devices:', error)
        setAllDevices([])
      }
    }
    
    loadDevices()
  }, [apiDevicesResponse])

  // Load logs based on selected device and date
  const loadLogs = async () => {
    setIsLoading(true)
    try {
      const dateString = selectedDate?.toISOString().split('T')[0] // YYYY-MM-DD format
      const params = new URLSearchParams()
      
      if (selectedDevice !== "all") {
        params.append('device_id', selectedDevice)
      }
      if (dateString) {
        params.append('date', dateString)
      }
      
      console.log('Loading logs with params:', params.toString())
      
      // Call the backend API for logs
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/logs?${params.toString()}`)
      
      if (response.ok) {
        const data = await response.json()
        const logEntries: LogEntry[] = data.logs || []
        setLogs(logEntries)
        setFilteredLogs(logEntries)
        console.log('Loaded logs:', logEntries.length)
      } else {
        console.warn('Failed to fetch logs:', response.status)
        setLogs([])
        setFilteredLogs([])
      }
    } catch (error) {
      console.error('Failed to load logs:', error)
      // For development, show a sample message when API is not available
      console.log('API not available, showing empty state')
      setLogs([])
      setFilteredLogs([])
    } finally {
      setIsLoading(false)
    }
  }

  // Load logs when device or date changes
  useEffect(() => {
    if (selectedDevice && selectedDate) {
      loadLogs()
    }
  }, [selectedDevice, selectedDate])

  const getLogIcon = (level: string) => {
    switch (level) {
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "info":
      default:
        return <Clock className="w-4 h-4 text-blue-500" />
    }
  }

  const getLogBadgeColor = (level: string) => {
    switch (level) {
      case "error":
        return "bg-red-100 text-red-800 border-red-200"
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "success":
        return "bg-green-100 text-green-800 border-green-200"
      case "info":
      default:
        return "bg-blue-100 text-blue-800 border-blue-200"
    }
  }

  const children = (
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
                    <FileText className="w-6 h-6 text-black" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold text-white tracking-tight">System Logs</h1>
                    <p className="text-gray-300 text-lg mt-1">Monitor system activity and troubleshoot issues</p>
                  </div>
                </div>
                
                {/* Live Status Indicator */}
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                    <div className="relative">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping opacity-75"></div>
                    </div>
                    <span className="text-white text-sm font-medium">Live Monitoring</span>
                  </div>
                  
                  <div className="text-white/60 text-sm">
                    Last updated: {new Date().toLocaleTimeString()}
                  </div>
                </div>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                <div className="flex items-center space-x-4">
                  <Button 
                    className="bg-white/10 text-white border-white/20 hover:bg-white/20 rounded-2xl px-4 py-2"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </Button>
                  <Button 
                    className="bg-white text-black hover:bg-gray-100 font-semibold px-6 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] border-0"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Export Logs
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Search Bar and Platform Switcher */}
            <div className="mt-8">
              <div className="flex items-center justify-between">
                <div className="flex-1 max-w-md">
                  <GlobalSearchBar placeholder="Search logs..." />
                </div>
                <div className="flex items-center space-x-4">
                  <PlatformSwitch />
                </div>
              </div>
            </div>
          </div>
        </div>
      </PlatformHeader>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Filter Controls */}
        <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-8">
          <div className="flex items-center justify-center">
            <div className="flex items-center space-x-12">
              {/* Device Selection */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-gray-700 block text-center">Device</label>
                <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                  <SelectTrigger className="w-64 h-14 rounded-xl border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm px-4 min-h-[56px]">
                    <SelectValue placeholder="Select device" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">
                      <div className="flex items-center space-x-3 py-1">
                        <div className="w-3 h-3 bg-gray-400 rounded-full" />
                        <span>All Devices</span>
                      </div>
                    </SelectItem>
                    {allDevices.map((device) => (
                      <SelectItem key={device.id} value={device.id.toString()}>
                        <div className="flex items-center space-x-3 py-1">
                          <Smartphone className="w-4 h-4" />
                          <span>{device.name}</span>
                          <div className={`w-3 h-3 rounded-full ${
                            device.status === 'connected' ? 'bg-green-500' : 'bg-gray-400'
                          }`} />
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Date Selection */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-gray-700 block text-center">Date</label>
                <Button
                  variant="outline"
                  onClick={() => setIsCalendarOpen(true)}
                  className="w-64 h-14 rounded-xl border-gray-200 hover:border-gray-300 text-sm justify-start px-4"
                >
                  <CalendarIcon className="w-5 h-5 mr-3" />
                  {selectedDate ? selectedDate.toLocaleDateString() : "Select date"}
                </Button>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-gray-700 block text-center opacity-0">Actions</label>
                <div className="flex items-center space-x-3">
                  <Button 
                    onClick={loadLogs}
                    disabled={isLoading}
                    className="h-14 px-8 bg-black text-white hover:bg-gray-800 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    {isLoading ? (
                      <div className="flex items-center space-x-2">
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        <span>Loading...</span>
                      </div>
                    ) : (
                      <>
                        <RefreshCw className="w-5 h-5 mr-2" />
                        Refresh Logs
                      </>
                    )}
                  </Button>
                  
                  <Button 
                    variant="outline"
                    className="h-14 px-6 rounded-xl border-gray-200 hover:border-gray-300 font-semibold"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Logs Display */}
        <div className="bg-white rounded-3xl shadow-lg border border-gray-100 min-h-[600px]">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-4 h-4 text-gray-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Logs for {selectedDevice === "all" ? "All Devices" : allDevices.find(d => d.id.toString() === selectedDevice)?.name || "Unknown Device"}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {selectedDate ? selectedDate.toLocaleDateString() : "No date selected"}
                  </p>
                </div>
              </div>
              
              <Badge className="bg-blue-100 text-blue-800 border-blue-200 text-sm font-semibold px-3 py-1">
                {filteredLogs.length} entries
              </Badge>
            </div>

            {/* Logs List */}
            <div className="space-y-3">
              {isLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center space-y-4">
                    <div className="relative">
                      <div className="w-16 h-16 border-4 border-gray-200 rounded-full animate-spin border-t-black mx-auto"></div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-lg font-semibold text-gray-900">Loading logs...</div>
                      <div className="text-sm text-gray-500">Fetching logs for selected device and date</div>
                    </div>
                  </div>
                </div>
              ) : filteredLogs.length === 0 ? (
                <div className="text-center py-20">
                  <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mb-4 mx-auto">
                    <FileText className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">No logs found</h3>
                  <p className="text-gray-500 mb-4">
                    {selectedDevice === "all" 
                      ? "No logs available for the selected date"
                      : `No logs found for ${allDevices.find(d => d.id.toString() === selectedDevice)?.name || "this device"} on ${selectedDate?.toLocaleDateString()}`
                    }
                  </p>
                  <Button 
                    onClick={loadLogs}
                    variant="outline"
                    className="rounded-lg"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              ) : (
                filteredLogs.map((log) => (
                  <Card key={log.id} className="hover:shadow-md transition-shadow border border-gray-100">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3 flex-1">
                          <div className="flex-shrink-0 mt-1">
                            {getLogIcon(log.level)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-3 mb-2">
                              <Badge className={`${getLogBadgeColor(log.level)} text-xs font-semibold`}>
                                {log.level.toUpperCase()}
                              </Badge>
                              <span className="text-sm text-gray-500">{log.source}</span>
                              <span className="text-sm text-gray-400">{log.timestamp}</span>
                              {log.device_name && (
                                <span className="text-xs text-gray-400">• {log.device_name}</span>
                              )}
                            </div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-1">{log.message}</h4>
                            <p className="text-xs text-gray-600">{log.details}</p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Calendar Popup */}
        <CalendarPopup
          open={isCalendarOpen}
          onOpenChange={setIsCalendarOpen}
          selectedDate={selectedDate}
          onDateSelect={setSelectedDate}
        />
      </div>
    </div>
  )

  return (
    <LicenseBlocker action="access system logs" platform="instagram" children={children} />
  )
}
