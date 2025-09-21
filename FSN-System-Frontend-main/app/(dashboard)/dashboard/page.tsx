"use client"

import { StatCard } from "@/components/stat-card"
import { DataListCard } from "@/components/data-list-card"
import { FollowersGrowthChart } from "@/components/charts/followers-growth-chart"
import { StatusBadge } from "@/components/status-badge"
import { LicenseStatus } from "@/components/license-status"
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { LicenseBlocker } from "@/components/license-blocker"
import { HeroCard } from "@/components/hero-card"
import { Button } from "@/components/ui/button"
import { Smartphone, AlertTriangle, Clock, Play, RefreshCw, Zap, Eye, FileText, BarChart3 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState, useEffect } from "react"
import { useDevices, useDeviceStats } from "@/lib/hooks/use-devices"
import { useAccounts } from "@/lib/hooks/use-accounts"
import { useJobs } from "@/lib/hooks/use-jobs"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"

export default function DashboardPage() {
  const router = useRouter()
  
  // Use real API hooks
  const { data: devicesResponse, isLoading: devicesLoading } = useDevices()
  const { data: accountsData } = useAccounts()
  const { data: jobsData } = useJobs()
  const { stats: deviceStats, isLoading: statsLoading } = useDeviceStats()
  
  // Handle both array format and paginated response format
  const devices = Array.isArray(devicesResponse) 
    ? devicesResponse 
    : devicesResponse?.devices || []
  
  // Extract items from paginated responses with defensive programming
  const accounts = Array.isArray(accountsData?.items) ? accountsData.items : []
  const jobs = Array.isArray(jobsData?.items) ? jobsData.items : []
  
  // Calculate running devices from API data
  const runningDevices = devices.filter(device => device.status === 'active')
  
  console.log('Dashboard device stats:', { 
    totalDevices: devices.length, 
    runningDevices: runningDevices.length,
    deviceStatuses: devices.map(d => ({ id: d.id, name: d.name, status: d.status })),
    apiDevices: devices,
    localDevices: licenseAwareStorageService.getDevices()
  })
  
  // Calculate today's posts and views from real job data
  const today = new Date().toISOString().split('T')[0]
  const todayJobs = jobs.filter(job => 
    job && job.created_at && job.created_at.startsWith(today)
  )
  const todayPosts = todayJobs.filter(job => 
    job && (job.type === 'instagram_post_reel' || job.type === 'threads_create_post')
  ).length
  const todayViews = todayJobs.reduce((total, job) => {
    return total + (job?.result?.views || 0)
  }, 0)
  
  const isLoading = devicesLoading || statsLoading || !accountsData || !jobsData

  // Transform running devices for display
  const runningDevicesList = runningDevices.map((device) => {
    // Calculate device-specific stats
    const deviceJobs = jobs.filter(job => job.account_id && accounts.find(acc => acc.id === job.account_id)?.device_id === device.id)
    const devicePosts = deviceJobs.filter(job => 
      job.type === 'instagram_post_reel' || job.type === 'threads_create_post'
    ).length
    const deviceViews = deviceJobs.reduce((total, job) => total + (job.result?.views || 0), 0)
    
    return {
      id: device.id.toString(),
      icon: <Smartphone className="w-4 h-4" />,
      title: device.name,
      subtitle: `Total Posts: ${devicePosts} • Total Views: ${deviceViews.toLocaleString()}`,
      meta: `iOS ${device.ios_version || 'Unknown'} • ${device.model || 'Unknown Model'}`,
      badge: (
        <StatusBadge status="active">
          Running
        </StatusBadge>
      ),
      action: {
        label: "View",
        onClick: () => router.push(`/devices/${device.id}`)
      },
    }
  })

  // Next Up task state
  const [nextTask, setNextTask] = useState<{
    account: string;
    action: string;
    countdown: number;
    device: string;
    deviceId: string;
  } | null>(null)

  // Generate next task from running devices and their accounts
  useEffect(() => {
    if (runningDevices.length === 0 || accounts.length === 0) {
      setNextTask(null)
      return
    }

    // Find accounts assigned to running devices
    const runningDeviceIds = runningDevices.map(d => d.id)
    const assignedAccounts = accounts.filter(account => 
      account.device_id && runningDeviceIds.includes(account.device_id)
    )

    if (assignedAccounts.length === 0) {
      setNextTask(null)
      return
    }

    // Find the first account that should be processed next
    const nextAccount = assignedAccounts[0] // For now, just take the first one
    const device = runningDevices.find(d => d.id === nextAccount.device_id)
    
    if (!device) {
      setNextTask(null)
      return
    }

    // Determine the action based on platform
    let action = "Instagram Post Creation"
    if (nextAccount.platform === "threads") {
      action = "Threads Post Creation"
    } else if (nextAccount.platform === "both") {
      action = "Multi-Platform Post Creation"
    }

    // Set up the next task
    setNextTask({
      account: nextAccount.username || "Unknown",
      action: action,
      countdown: 120, // 2 minutes countdown
      device: device.name,
      deviceId: device.id.toString()
    })

    // Countdown timer
    const interval = setInterval(() => {
      setNextTask(prev => {
        if (!prev) return null
        if (prev.countdown <= 1) {
          // Task completed, find next account
          const currentIndex = assignedAccounts.findIndex(acc => 
            acc.username === prev.account
          )
          const nextIndex = (currentIndex + 1) % assignedAccounts.length
          const nextAccount = assignedAccounts[nextIndex]
          const device = runningDevices.find(d => d.id === nextAccount.device_id)
          
          if (!device) return null

          let action = "Instagram Post Creation"
          if (nextAccount.platform === "threads") {
            action = "Threads Post Creation"
          } else if (nextAccount.platform === "both") {
            action = "Multi-Platform Post Creation"
          }

          return {
            account: nextAccount.username || "Unknown",
            action: action,
            countdown: 120,
            device: device.name,
            deviceId: device.id.toString()
          }
        }
        return { ...prev, countdown: prev.countdown - 1 }
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [runningDevices, accounts])

  // Generate queue items from running devices and their accounts
  const queueItems = (() => {
    if (runningDevices.length === 0 || accounts.length === 0) return []
    
    const runningDeviceIds = runningDevices.map(d => d.id)
    
    // Find accounts assigned to running devices
    const assignedAccounts = accounts.filter(account => 
      account.device_id && runningDeviceIds.includes(account.device_id)
    )

    return assignedAccounts.map((account, index) => {
      const device = runningDevices.find(d => d.id === account.device_id)
      
      if (!device) return null

      let action = "Instagram Post Creation"
      let icon = <FileText className="w-4 h-4" />
      
      if (account.platform === "threads") {
        action = "Threads Post Creation"
        icon = <Play className="w-4 h-4" />
      } else if (account.platform === "both") {
        action = "Multi-Platform Post Creation"
        icon = <Clock className="w-4 h-4" />
      }

      const username = account.username || "Unknown"
      
      return {
        id: account.id,
        icon: icon,
        title: action,
        subtitle: `Account: @${username} • Device: ${device.name}`,
        badge: index === 0 ? 
          <StatusBadge status="pending">Next</StatusBadge> : 
          <StatusBadge status="pending">Queued</StatusBadge>,
        action: {
          label: "View",
          onClick: () => router.push('/running')
        },
      }
    }).filter((item): item is NonNullable<typeof item> => item !== null) // Remove null entries with proper typing
  })()

  // Calculate queue stats
  const queueStats = {
    pending: queueItems.filter(j => j && j.badge.props.status === 'pending').length,
    running: queueItems.filter(j => j && j.badge.props.status === 'running').length,
    total: queueItems.length,
  }

  return (
    <LicenseBlocker action="access the dashboard">
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
                      <BarChart3 className="w-6 h-6 text-black" />
                    </div>
                    <div>
                      <h1 className="text-4xl font-bold text-white tracking-tight">Dashboard</h1>
                      <p className="text-gray-300 text-lg mt-1">Monitor your social media automation performance</p>
                    </div>
                  </div>
                  
                  {/* Live Status Indicator */}
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                      <div className="relative">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping opacity-75"></div>
                      </div>
                      <span className="text-white text-sm font-medium">Live Data</span>
                    </div>
                    
                    <div className="text-white/60 text-sm">
                      Last updated: {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                  <LicenseStatus />
                </div>
              </div>
              
              {/* Search Bar and Platform Switcher - Integrated into header */}
              <div className="mt-8">
                <div className="flex items-center justify-between">
                  {/* Search */}
                  <div className="flex-1 max-w-md">
                    <GlobalSearchBar placeholder="Search devices, accounts, jobs..." />
                  </div>

                  {/* Right side */}
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
              <div className="absolute inset-0 bg-gradient-to-br from-green-50 to-emerald-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <div className="text-green-600 text-xl font-bold">▶</div>
                  </div>
                  <div className="text-3xl font-bold text-green-600">{isLoading ? "..." : runningDevices.length}</div>
                </div>
                <div className="space-y-1">
                  <div className="font-semibold text-gray-900">Running Devices</div>
                  <div className="text-sm text-gray-500">{isLoading ? "..." : devices.length} total devices</div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <div className="text-blue-600 text-xl font-bold">📝</div>
                  </div>
                  <div className="text-3xl font-bold text-blue-600">{isLoading ? "..." : todayPosts}</div>
                </div>
                <div className="space-y-1">
                  <div className="font-semibold text-gray-900">Posts Today</div>
                  <div className="text-sm text-gray-500">Total posts created today</div>
                </div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-50 to-violet-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <div className="text-purple-600 text-xl font-bold">👁</div>
                  </div>
                  <div className="text-3xl font-bold text-purple-600">{isLoading ? "..." : todayViews.toLocaleString()}</div>
                </div>
                <div className="space-y-1">
                  <div className="font-semibold text-gray-900">Views Today</div>
                  <div className="text-sm text-gray-500">Total views across all posts</div>
                </div>
              </div>
            </div>
          </div>

          {/* Followers Growth Chart */}
          <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6">
            <FollowersGrowthChart key="followers-chart" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left column - Running Devices */}
            <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Running Devices</h2>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => router.push('/running')}
                  className="bg-black text-white hover:bg-gray-800 border-black rounded-2xl px-4 py-2 font-semibold"
                >
                  View All
                </Button>
              </div>
              <DataListCard
                title=""
                items={runningDevicesList}
                isLoading={isLoading}
              />
            </div>

            {/* Right column - Queue Status */}
            <div className="space-y-6">
              {/* Next Up Section */}
              {nextTask && (
                <div className="bg-gradient-to-br from-black to-gray-900 rounded-3xl shadow-2xl p-8 border border-gray-800 text-white">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-white">Next Up</h3>
                    <div className="flex items-center space-x-3 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
                      <div className="text-white text-lg font-bold">🕐</div>
                      <span className="text-lg font-bold text-white">
                        {Math.floor(nextTask.countdown / 60)}:{(nextTask.countdown % 60).toString().padStart(2, '0')}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-lg">
                        <div className="text-black text-xl font-bold">📝</div>
                      </div>
                      <div className="flex-1">
                        <div className="text-lg font-bold text-white">{nextTask.action}</div>
                        <div className="text-gray-300 mt-1">
                          Account: {nextTask.account} • Device: {nextTask.device}
                        </div>
                      </div>
                    </div>
                    <div className="mt-6">
                      <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
                        <div 
                          className="bg-white h-3 rounded-full transition-all duration-1000 relative"
                          style={{ width: `${((120 - nextTask.countdown) / 120) * 100}%` }}
                        >
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-300 mt-2">
                        Progress: {Math.round(((120 - nextTask.countdown) / 120) * 100)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-gray-900">Queue Status</h2>
                  <div className="text-sm text-gray-500">
                    {`${queueStats.pending} pending • ${queueStats.running} running • ${queueStats.total} total`}
                  </div>
                </div>
                <DataListCard
                  title=""
                  items={queueItems}
                  isLoading={false}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </LicenseBlocker>
  )
}
