"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FileText, AlertTriangle, CheckCircle, XCircle, Clock, RefreshCw, Download, Filter } from "lucide-react"
import { HeroCard } from "@/components/hero-card"
import { LicenseBlocker } from "@/components/license-blocker"
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"

// Mock log data - TODO: Replace with real API data
const logs = [
  {
    id: "1",
    timestamp: "2024-01-15 14:32:15",
    level: "error" as const,
    source: "Device Manager",
    message: "Failed to connect to iPhone 15 Pro - Device 1",
    details: "Connection timeout after 30 seconds. Check USB connection and device trust settings.",
  },
  {
    id: "2", 
    timestamp: "2024-01-15 14:30:22",
    level: "info" as const,
    source: "Automation Engine",
    message: "Started automation job for @lifestyle_blogger",
    details: "Template: Daily Posting, Device: iPhone 15 Pro - Device 1",
  },
  {
    id: "3",
    timestamp: "2024-01-15 14:28:45",
    level: "warning" as const,
    source: "Account Manager",
    message: "Account @fitness_guru requires verification",
    details: "Instagram checkpoint detected. Manual verification may be required.",
  },
  {
    id: "4",
    timestamp: "2024-01-15 14:25:12",
    level: "success" as const,
    source: "Post Manager",
    message: "Successfully posted content for @travel_enthusiast",
    details: "Post ID: 3142857264, Engagement: 45 likes, 12 comments",
  },
  {
    id: "5",
    timestamp: "2024-01-15 14:20:33",
    level: "info" as const,
    source: "System",
    message: "Backend server started successfully",
    details: "API server listening on port 8000, WebSocket server on port 8001",
  }
]

const errors = logs.filter(log => log.level === "error")

export default function LogsPage() {
  const [selectedTab, setSelectedTab] = useState("all")
  const [filteredLogs, setFilteredLogs] = useState(logs)

  useEffect(() => {
    if (selectedTab === "all") {
      setFilteredLogs(logs)
    } else {
      setFilteredLogs(logs.filter(log => log.level === selectedTab))
    }
  }, [selectedTab])

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
      {/* Main Header Section - Dark Background */}
      <div className="relative overflow-hidden bg-gradient-to-r from-black via-gray-900 to-black">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')] opacity-10"></div>
        
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
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Enhanced Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-red-50 to-rose-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-red-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
                <div className="text-3xl font-bold text-red-600">{logs.filter(l => l.level === 'error').length}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Errors</div>
                <div className="text-sm text-gray-500">Critical issues</div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-50 to-amber-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <AlertTriangle className="w-6 h-6 text-yellow-600" />
                </div>
                <div className="text-3xl font-bold text-yellow-600">{logs.filter(l => l.level === 'warning').length}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Warnings</div>
                <div className="text-sm text-gray-500">Attention needed</div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-green-50 to-emerald-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div className="text-3xl font-bold text-green-600">{logs.filter(l => l.level === 'success').length}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Success</div>
                <div className="text-sm text-gray-500">Completed tasks</div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <Clock className="w-6 h-6 text-blue-600" />
                </div>
                <div className="text-3xl font-bold text-blue-600">{logs.filter(l => l.level === 'info').length}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Info</div>
                <div className="text-sm text-gray-500">General activity</div>
              </div>
            </div>
          </div>
        </div>

        {/* Logs Content */}
        <div className="space-y-6">
          <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
            <TabsList className="grid w-full grid-cols-5 bg-white rounded-2xl p-1 shadow-lg border border-gray-100">
              <TabsTrigger value="all" className="rounded-xl data-[state=active]:bg-black data-[state=active]:text-white">
                All Logs
              </TabsTrigger>
              <TabsTrigger value="error" className="rounded-xl data-[state=active]:bg-red-500 data-[state=active]:text-white">
                Errors
              </TabsTrigger>
              <TabsTrigger value="warning" className="rounded-xl data-[state=active]:bg-yellow-500 data-[state=active]:text-white">
                Warnings
              </TabsTrigger>
              <TabsTrigger value="success" className="rounded-xl data-[state=active]:bg-green-500 data-[state=active]:text-white">
                Success
              </TabsTrigger>
              <TabsTrigger value="info" className="rounded-xl data-[state=active]:bg-blue-500 data-[state=active]:text-white">
                Info
              </TabsTrigger>
            </TabsList>

            <TabsContent value={selectedTab} className="mt-6">
              <div className="space-y-4">
                {filteredLogs.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mb-4 mx-auto">
                      <FileText className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No logs found</h3>
                    <p className="text-gray-500">No {selectedTab === "all" ? "" : selectedTab} logs available for the selected filter.</p>
                  </div>
                ) : (
                  filteredLogs.map((log) => (
                    <Card key={log.id} className="hover:shadow-lg transition-shadow border border-gray-100">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-4 flex-1">
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
                              </div>
                              <h4 className="text-base font-semibold text-gray-900 mb-1">{log.message}</h4>
                              <p className="text-sm text-gray-600">{log.details}</p>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )

  return (
    <LicenseBlocker action="access system logs" platform="instagram" children={children} />
  )
}
