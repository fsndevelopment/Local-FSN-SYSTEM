"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Play as PlayIcon } from "lucide-react"
// Keep the original SVG icons for buttons, only fix the statistics dots
const Play = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>▶</div>
)

const Pause = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>⏸</div>
)

const Square = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>⏹</div>
)

const AlertTriangle = ({ className = "w-4 h-4", ...props }: any) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`} {...props}>⚠</div>
)

const CheckCircle = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>✓</div>
)

const Clock = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>🕐</div>
)

const Users = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>👥</div>
)

const Settings = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>⚙</div>
)

const Info = ({ className = "w-4 h-4" }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`}>ℹ</div>
)

const RefreshCw = ({ className = "w-4 h-4", ...props }: any) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`} {...props}>↻</div>
)

const Usb = ({ className = "w-4 h-4", ...props }: any) => (
  <div className={`${className} flex items-center justify-center text-current font-bold`} {...props}>🔌</div>
)

const Smartphone = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect width="14" height="20" x="5" y="2" rx="2" ry="2"/>
    <path d="M12 18h.01"/>
  </svg>
)
import { RunningDevice, Template } from "@/lib/types"
import { cn } from "@/lib/utils"
import { useDevices } from "@/lib/hooks/use-devices"
import { useJobs } from "@/lib/hooks/use-jobs"
import { LicenseBlocker } from "@/components/license-blocker"
import { HeroCard } from "@/components/hero-card"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { useWebSocketContext } from "@/lib/providers/websocket-provider"
import { useRef } from "react"
import { AddDeviceDialog } from "@/components/add-device-dialog"

// Wave Animation Component
const WaveAnimation = () => (
  <div className="flex space-x-1 items-center">
    <div className="w-1 h-3 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
    <div className="w-1 h-3 bg-current rounded-full animate-bounce" style={{ animationDelay: '200ms', animationDuration: '1s' }}></div>
    <div className="w-1 h-3 bg-current rounded-full animate-bounce" style={{ animationDelay: '400ms', animationDuration: '1s' }}></div>
  </div>
)

// Premium Morphing Button Component with Black/White Aesthetic
const MorphingButton = ({ device, startingDevices, stoppingDevices, onStart, onPause, onStop }: {
  device: any,
  startingDevices: Set<string>,
  stoppingDevices: Set<string>,
  onStart: (id: string) => void,
  onPause: (id: string) => void,
  onStop: (id: string) => void
}) => {
  const isStarting = startingDevices.has(device.id)
  const isStopping = stoppingDevices.has(device.id)
  const isRunning = device.status === "running"
  const isStopped = device.status === "stopped"
  const [isAnimating, setIsAnimating] = useState(false)
  
  // Trigger animation when transitioning to running state
  useEffect(() => {
    if (isRunning && !isStopping) {
      setIsAnimating(true)
      const timer = setTimeout(() => setIsAnimating(false), 800)
      return () => clearTimeout(timer)
    }
  }, [isRunning, isStopping])
  
  if (isStopped && !isStarting) {
    // Elegant Start Button - Black/White Theme
    return (
      <Button
        onClick={() => onStart(device.id)}
        className="w-full h-14 bg-black text-white hover:bg-gray-800 font-semibold shadow-2xl hover:shadow-3xl transition-all duration-500 transform hover:scale-[1.02] active:scale-[0.98] rounded-2xl border-0"
      >
        <div className="flex items-center justify-center space-x-3">
          <div className="text-white text-lg font-bold">▶</div>
          <span className="text-lg">Start Automation</span>
        </div>
      </Button>
    )
  }
  
  if (isStarting) {
    // Sophisticated Loading State
    return (
      <div className="relative w-full">
        <Button
          disabled
          className="w-full h-14 bg-gradient-to-r from-gray-600 to-gray-700 text-white font-semibold shadow-2xl rounded-2xl border-0 cursor-not-allowed"
        >
          <div className="flex items-center justify-center space-x-3">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="text-lg">Initializing...</span>
          </div>
        </Button>
        {/* Elegant border animation */}
        <div className="absolute inset-0 rounded-2xl border-2 border-white/20 animate-pulse"></div>
      </div>
    )
  }
  
  if (isRunning && !isStopping) {
    // Premium Split Button Layout
    return (
      <div className="relative w-full">
        <div className={`flex space-x-3 transition-all duration-800 ${isAnimating ? 'animate-in slide-in-from-top-4 fade-in' : ''}`}>
          {/* Elegant Pause Button */}
          <Button
            onClick={() => onPause(device.id)}
            className="flex-1 h-14 bg-white text-black hover:bg-gray-50 border-2 border-black font-semibold shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] rounded-2xl"
          >
            <div className="flex items-center justify-center space-x-2">
              <div className="w-5 h-5 bg-black rounded-md flex items-center justify-center">
                <Pause className="w-3 h-3" />
              </div>
              <span>Pause</span>
            </div>
          </Button>
          
          {/* Elegant Stop Button */}
          <Button
            onClick={() => onStop(device.id)}
            className="flex-1 h-14 bg-black text-white hover:bg-gray-800 border-2 border-black font-semibold shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] rounded-2xl"
          >
            <div className="flex items-center justify-center space-x-2">
              <div className="w-5 h-5 bg-white rounded-md flex items-center justify-center">
                <Square className="w-3 h-3" />
              </div>
              <span>Stop</span>
            </div>
          </Button>
        </div>
        
        {/* Sophisticated split animation overlay */}
        {isAnimating && (
          <div className="absolute inset-0 flex space-x-3">
            <div className="flex-1 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl animate-pulse"></div>
            <div className="flex-1 bg-gradient-to-r from-black/10 to-black/5 rounded-2xl animate-pulse"></div>
          </div>
        )}
      </div>
    )
  }
  
  if (isStopping) {
    // Refined Stopping State
    return (
      <div className="relative w-full">
        <Button
          disabled
          className="w-full h-14 bg-gradient-to-r from-gray-700 to-gray-800 text-white font-semibold shadow-2xl rounded-2xl border-0 cursor-not-allowed opacity-90"
        >
          <div className="flex items-center justify-center space-x-3">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="text-lg">Stopping...</span>
          </div>
        </Button>
        <div className="absolute inset-0 rounded-2xl border-2 border-red-300/30 animate-pulse"></div>
      </div>
    )
  }
  
  // Error/Retry State with Black/White Theme
  return (
    <Button
      onClick={() => onStart(device.id)}
      className="w-full h-14 bg-gradient-to-r from-gray-800 to-black text-white hover:from-gray-700 hover:to-gray-900 font-semibold shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] rounded-2xl border-0"
    >
      <div className="flex items-center justify-center space-x-3">
        <div className="w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
          <RefreshCw className="w-3 h-3" />
        </div>
        <span className="text-lg">Retry</span>
      </div>
    </Button>
  )
}

export default function RunningPage() {
  // Use API hooks
  const { data: apiDevicesResponse, isLoading, refetch } = useDevices()
  const { data: jobsData } = useJobs()
  
  // Handle both array format and paginated response format
  const apiDevices = Array.isArray(apiDevicesResponse) 
    ? apiDevicesResponse 
    : apiDevicesResponse?.devices || []
  
  // Extract jobs from paginated response
  const jobs = Array.isArray(jobsData?.items) ? jobsData.items : []
  
  // Load accounts, devices, templates, and device template assignments from license-aware storage
  const [accounts, setAccounts] = useState<any[]>([])
  const [mockDevices, setMockDevices] = useState<any[]>([])
  const [templates, setTemplates] = useState<any[]>([])
  const [deviceTemplates, setDeviceTemplates] = useState<Record<string, string>>({})
  
  // Device loading states
  const [startingDevices, setStartingDevices] = useState<Set<string>>(new Set())
  const [stoppingDevices, setStoppingDevices] = useState<Set<string>>(new Set())
  const [isAddDeviceDialogOpen, setIsAddDeviceDialogOpen] = useState(false)
  
  // Real-time progress tracking
  const [deviceProgress, setDeviceProgress] = useState<Record<string, { progress: number, currentAction: string, checkpoint: number, timestamp?: number }>>({})  
  
  // Error dialog state
  const [errorDialog, setErrorDialog] = useState<{
    isOpen: boolean
    title: string
    message: string
    deviceId?: string
    showTroubleshooting?: boolean
  }>({
    isOpen: false,
    title: '',
    message: '',
    showTroubleshooting: false
  })
  
  // WebSocket integration for real-time updates
  // Use jobs WebSocket for job updates instead of main WebSocket
  const [ws, setWs] = useState<WebSocket | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  
  // Keep the main WebSocket for device status updates
  const websocket = useWebSocketContext()
  
  // Debug WebSocket connection
  useEffect(() => {
    console.log('🔌 WebSocket Debug:', {
      websocket,
      state: websocket?.state,
      isConnected: websocket?.isConnected,
      isConnecting: websocket?.isConnecting,
      hasError: websocket?.hasError,
      lastMessage: websocket?.lastMessage
    })
    
    // Log WebSocket connection status
    if (websocket?.state === 'connected') {
      console.log('✅ WebSocket is CONNECTED')
    } else if (websocket?.state === 'connecting') {
      console.log('🔄 WebSocket is CONNECTING...')
    } else if (websocket?.state === 'disconnected') {
      console.log('❌ WebSocket is DISCONNECTED')
    } else if (websocket?.hasError) {
      console.log('❌ WebSocket has ERROR:', websocket.hasError)
    }
  }, [websocket?.state, websocket?.lastMessage])
  
  // Use the existing main WebSocket for job updates (no separate Jobs WebSocket needed)
  
  // Polling for job updates as backup
  useEffect(() => {
    let interval: NodeJS.Timeout
    
    const pollJobUpdates = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/jobs', {
          signal: AbortSignal.timeout(5000) // 5 second timeout
        })
        if (response.ok) {
          const data = await response.json()
          console.log('📊 POLLING RESPONSE:', data)
          
          // Mac Agent returns { active_jobs: [...], completed_jobs: [...] }
          console.log('📊 ALL ACTIVE JOBS:', data.active_jobs)
          
          // Check what status the jobs actually have
          if (data.active_jobs && data.active_jobs.length > 0) {
            data.active_jobs.forEach((job: any, index: number) => {
              console.log(`📊 JOB ${index}:`, {
                id: job.id,
                status: job.status,
                device_id: job.device_id,
                progress: job.progress,
                current_step: job.current_step,
                message: job.message
              })
            })
          }
          
          const runningJobs = data.active_jobs?.filter((job: any) => 
            job.status === 'executing' || 
            job.status === 'running' || 
            job.status === 'initializing' ||
            job.status === 'active' ||
            job.status === 'pending'  // Include pending status
          ) || []
          
          console.log('📊 FOUND RUNNING JOBS:', runningJobs.length, runningJobs)
          
          if (runningJobs.length > 0) {
            const latestJob = runningJobs[0]
            console.log('📊 LATEST JOB:', latestJob)
            
            if (latestJob.device_id === 4 || latestJob.device_id === "4") {
              console.log('📊 POLLING JOB UPDATE FOR DEVICE 4:', {
                jobId: latestJob.id,
                progress: latestJob.progress || 0,
                currentStep: latestJob.current_step || latestJob.message || 'Processing...',
                status: latestJob.status,
                timestamp: new Date().toISOString()
              })
              
              setDeviceProgress(prev => {
                const currentState = prev["4"]
                const newState = {
                  ...prev,
                  "4": {
                    progress: latestJob.progress || 0,
                    // Only update currentAction if we don't have recent WebSocket data (within 5 seconds)
                    currentAction: (currentState?.timestamp && Date.now() - currentState.timestamp < 5000) 
                      ? currentState.currentAction  // Keep WebSocket data if recent
                      : (latestJob.current_step || latestJob.message || 'Processing...'), // Use polling data only if no recent WebSocket
                    checkpoint: Math.floor((latestJob.progress || 0) / 7.69),
                    timestamp: Date.now()
                  }
                }
                console.log('📊 SETTING NEW STATE (polling):', newState)
                return newState
              })
              
              setForceRender(prev => prev + 1)
            }
          } else {
            console.log('📊 NO RUNNING JOBS FOUND')
          }
        }
      } catch (error) {
        // Only log network errors occasionally to avoid spam
        if (error instanceof Error && error.name === 'AbortError') {
          console.warn('Job polling timeout - backend may be down')
        } else if (error instanceof TypeError && error.message.includes('fetch failed')) {
          console.warn('Backend connection failed - is local-backend.py running?')
        } else {
          console.error('Failed to poll job updates:', error)
        }
      }
    }
    
    // Poll every 2 seconds
    interval = setInterval(pollJobUpdates, 2000)
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [])
  
  useEffect(() => {
    const loadData = async () => {
      try {
        const savedAccounts = await licenseAwareStorageService.getAccounts()
        const savedDevices = licenseAwareStorageService.getDevices()
        const savedTemplates = await licenseAwareStorageService.getTemplates()
        const savedDeviceTemplates = licenseAwareStorageService.getDeviceTemplates()
        
        console.log('🔍 RUNNING PAGE - Loaded accounts:', savedAccounts)
        console.log('🔍 RUNNING PAGE - Loaded mock devices:', savedDevices)
        console.log('🔍 RUNNING PAGE - Loaded templates:', savedTemplates)
        console.log('🔍 RUNNING PAGE - Loaded device templates:', savedDeviceTemplates)
        
        setAccounts(savedAccounts)
        setMockDevices(savedDevices)
        setTemplates(savedTemplates)
        setDeviceTemplates(savedDeviceTemplates)
      } catch (error) {
        console.error('Failed to load data:', error)
        setAccounts([])
        setMockDevices([])
        setTemplates([])
        setDeviceTemplates({})
      }
    }
    
    loadData()
  }, [])
  
  // Combine API devices and mock devices
  const allDevices = [...apiDevices, ...mockDevices]
  
  // Convert all devices to RunningDevice format with job information
  // Force re-render when deviceProgress changes
  const [forceRender, setForceRender] = useState(0)
  
  const devices: RunningDevice[] = useMemo(() => allDevices.map((device: any) => {
    // Map API device status to running device status
    let status: "running" | "paused" | "stopped" | "error" = "stopped"
    
    if (device.status === "connected" || device.status === "active" || device.status === "running") {
      status = "running"
    } else if (device.status === "offline" || device.status === "stopped") {
      status = "stopped"
    } else if (device.status === "error") {
      status = "error"
    } else {
      status = "stopped"
    }
    
    // Get accounts assigned to this device
    const deviceAccounts = accounts.filter((account: any) => {
      if (!account.device) return false
      // Handle both string and number device IDs
      const match = account.device.toString() === device.id.toString()
      if (match) {
        console.log(`🔍 RUNNING PAGE - Found account ${account.username} for device ${device.name} (ID: ${device.id})`)
      }
      return match
    })
    
    console.log(`🔍 RUNNING PAGE - Device ${device.name} (ID: ${device.id}) has ${deviceAccounts.length} accounts assigned`)
    
    // Get jobs for this device
    const deviceJobs = jobs.filter((job: any) => job.device_id === device.id)
    const runningJobs = deviceJobs.filter((job: any) => job.status === 'running')
    const completedJobs = deviceJobs.filter((job: any) => job.status === 'completed')
    const failedJobs = deviceJobs.filter((job: any) => job.status === 'failed')
    
    // Get the most recent job for status
    const latestJob = deviceJobs.sort((a: any, b: any) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0]
    
    // Determine current step and last action
    let currentStep = "Idle"
    let lastAction = "No recent activity"
    
    if (runningJobs.length > 0) {
      currentStep = `Running ${runningJobs.length} job(s)`
      lastAction = `Executing ${latestJob?.type || 'automation'}`
    } else if (completedJobs.length > 0) {
      currentStep = `Completed ${completedJobs.length} job(s)`
      lastAction = `Last: ${latestJob?.type || 'automation'} completed`
    } else if (failedJobs.length > 0) {
      currentStep = `Failed ${failedJobs.length} job(s)`
      lastAction = `Last: ${latestJob?.type || 'automation'} failed`
    }
    
    return {
      id: device.id.toString(),
      name: device.name,
      status: status,
      accounts: deviceAccounts, // Accounts assigned to this device
      lastAction: lastAction,
      currentStep: currentStep,
      model: device.model || "Unknown Model",
      // Add job statistics
      jobStats: {
        total: deviceJobs.length,
        running: runningJobs.length,
        completed: completedJobs.length,
        failed: failedJobs.length
      }
    }
  }), [allDevices, jobs, accounts, deviceTemplates, templates, deviceProgress, forceRender])

  // Listen for WebSocket messages for real-time progress updates
  useEffect(() => {
    console.log('🔍 WebSocket useEffect triggered')
    console.log('🔍 websocket object:', websocket)
    console.log('🔍 websocket.lastMessage:', websocket?.lastMessage)
    
    if (!websocket?.lastMessage) {
      console.log('❌ No WebSocket message')
      return
    }
    
    const message = websocket.lastMessage
    console.log('🔥 RUNNING PAGE - Processing message:', message.type, message.timestamp)
    console.log('🔥 FULL MESSAGE DATA:', JSON.stringify(message, null, 2))
    
    // Log all message types to see what we're receiving
    console.log('📨 MESSAGE TYPE RECEIVED:', message.type)
    console.log('📨 MESSAGE KEYS:', Object.keys(message))
    
    // Handle job updates from Mac Agent (correct message type)
    if (message.type === 'job_update' && message.data) {
      const jobData = message.data
      const jobId = message.job_id
      
      console.log('🔄 JOB UPDATE RECEIVED:', {
        jobId,
        status: jobData.status,
        progress: jobData.progress,
        currentStep: jobData.current_step,
        timestamp: message.timestamp
      })
      
      // Get device ID from WebSocket message
      console.log('🔍 AVAILABLE DEVICES:', allDevices.map(d => ({ id: d.id, name: d.name, status: d.status })))
      console.log('🔍 JOB DATA:', jobData)
      
      // Use device_id from WebSocket message (backend now sends this)
      let targetDeviceId = jobData.device_id
      
      if (!targetDeviceId) {
        // Fallback: find the first running device
        const runningDevice = allDevices.find(d => d.status === "running")
        targetDeviceId = runningDevice?.id || "4" // fallback to 4
        console.log('⚠️ No device_id in WebSocket message, using running device:', targetDeviceId)
      } else {
        console.log('✅ Using device_id from WebSocket message:', targetDeviceId)
      }
      
      console.log('📊 UPDATING DEVICE PROGRESS:', {
        targetDeviceId,
        oldProgress: deviceProgress[targetDeviceId],
        newProgress: jobData.progress,
        newCurrentStep: jobData.current_step
      })
      
      // Force state update with timestamp
      setDeviceProgress(prev => {
        const newState = {
          ...prev,
          [targetDeviceId]: {
            progress: jobData.progress || 0,
            currentAction: jobData.current_step || '',
            checkpoint: Math.floor((jobData.progress || 0) / 7.69),
            timestamp: Date.now() // Add timestamp to force re-render
          }
        }
        console.log('✅ NEW DEVICE PROGRESS STATE:', newState)
        return newState
      })
    }
    
    // Handle device status updates
    if (message.type === 'device_status_update') {
      console.log('🔌 Device status update:', message)
      refetch()
    }
  }, [websocket?.lastMessage?.timestamp, websocket?.lastMessage?.type, refetch])

  const handleStart = async (deviceId: string) => {
    try {
      console.log('Starting device:', deviceId)
      
      // Add device to starting state
      setStartingDevices(prev => new Set([...prev, deviceId]))
      
      // Get assigned template for this device
      const assignedTemplateId = deviceTemplates[deviceId]
      let templateData = null
      
      if (assignedTemplateId) {
        const assignedTemplate = templates.find(t => t.id === assignedTemplateId)
        if (assignedTemplate) {
          console.log('🎯 Using assigned template:', assignedTemplate.name)
          templateData = {
            id: assignedTemplate.id,
            name: assignedTemplate.name,
            platform: assignedTemplate.platform,
            settings: {
              textPostsPerDay: assignedTemplate.textPostsPerDay || 0,
              textPostsFile: assignedTemplate.textPostsFile || "",
              textPostsFileContent: assignedTemplate.textPostsFileContent || "", // Include xlsx file content!
              photosPostsPerDay: assignedTemplate.photosPostsPerDay || 0,
              photosFolder: assignedTemplate.photosFolder || "",
              captionsFile: assignedTemplate.captionsFile || "",
              captionsFileContent: assignedTemplate.captionsFileContent || "",
              followsPerDay: assignedTemplate.followsPerDay || 0,
              likesPerDay: assignedTemplate.likesPerDay || 0,
              scrollingTimeMinutes: assignedTemplate.scrollingTimeMinutes || 0
            }
          }
        } else {
          console.log('⚠️ Assigned template not found:', assignedTemplateId)
        }
      } else {
        console.log('ℹ️ No template assigned to device:', deviceId)
      }
      
      const requestBody = {
        device_id: deviceId,
        job_type: "automation",
        template_data: templateData
      }
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices/${deviceId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })
      
      if (response.ok) {
        console.log('Device started successfully')
        if (templateData) {
          console.log('✅ Device started with template:', templateData.name)
        }
        refetch() // Refresh the device list
      } else {
        const error = await response.json()
        console.error('Failed to start device:', error.detail || error.message || error)
        
        // Show error dialog with troubleshooting tips
        setErrorDialog({
          isOpen: true,
          title: 'Device Failed to Start',
          message: error.detail || error.message || 'Unknown error occurred',
          deviceId: deviceId.toString(),
          showTroubleshooting: true
        })
      }
    } catch (error) {
      console.error('Error starting device:', error)
    } finally {
      // Remove device from starting state
      setStartingDevices(prev => {
        const newSet = new Set(prev)
        newSet.delete(deviceId)
        return newSet
      })
    }
  }

  const handlePause = async (deviceId: string) => {
    try {
      console.log('Pausing device:', deviceId)
      // For now, we'll just disconnect the device as a "pause"
      // TODO: Implement proper pause functionality in backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices/${deviceId}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        console.log('Device paused successfully')
        refetch() // Refresh the device list
      } else {
        const error = await response.json()
        console.error('Failed to pause device:', error.detail || error.message || error)
        alert(`Failed to pause device: ${error.detail || error.message || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error pausing device:', error)
    }
  }

  const handleStop = async (deviceId: string) => {
    try {
      console.log('Stopping device:', deviceId)
      
      // Add device to stopping state
      setStoppingDevices(prev => new Set([...prev, deviceId]))
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/devices/${deviceId}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        console.log('Device stopped successfully')
        refetch() // Refresh the device list
      } else {
        const error = await response.json()
        console.error('Failed to stop device:', error.detail || error.message || error)
        alert(`Failed to stop device: ${error.detail || error.message || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error stopping device:', error)
    } finally {
      // Remove device from stopping state
      setStoppingDevices(prev => {
        const newSet = new Set(prev)
        newSet.delete(deviceId)
        return newSet
      })
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Play />
      case "paused":
        return <Pause />
      case "stopped":
        return <Square />
      case "error":
        return <AlertTriangle />
      default:
        return <Square />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-100 text-green-800 border-green-200"
      case "paused":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "stopped":
        return "bg-gray-100 text-gray-800 border-gray-200"
      case "error":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getProgressValue = (device: RunningDevice) => {
    // Use real-time progress from WebSocket if available
    const realTimeProgress = deviceProgress[device.id]
    if (realTimeProgress) {
      return Math.min(realTimeProgress.progress, 100) // Cap at 100%
    }
    
    // Calculate real progress based on checkpoint data from WebSocket
    // For now, use job completion percentage until WebSocket provides checkpoint data
    if (device.jobStats && device.jobStats.total > 0) {
      const completionRate = device.jobStats.completed / device.jobStats.total
      return Math.round(completionRate * 100)
    }
    
    // Fallback to status-based progress
    switch (device.status) {
      case "running":
        return 15 // Show low progress when just started
      case "paused":
        return 30 // Show partial progress when paused
      case "stopped":
        return 0
      case "error":
        return 5 // Show minimal progress on error
      default:
        return 0
    }
  }
  
  const mapCheckpointToAction = (checkpoint: string): string => {
    // Map exact checkpoint names from Mac Agent logs to user-friendly descriptions
    const checkpointMap: Record<string, string> = {
      // Exact checkpoint names from the logs
      'launch_threads_from_desktop': 'Launching Threads App',
      'navigate_to_home_feed': 'Navigating to home feed',
      'click_create_tab': 'Opening create post',
      'enter_text': 'Entering text content',
      'add_image': 'Adding media files',
      'post_thread': 'Publishing the post',
      'handle_popups': 'Handling popups',
      'verify_post': 'Verifying post success',
      'return_safe_state': 'Returning to home',
      'navigate_to_profile': 'Navigating to profile',
      'extract_followers': 'Extracting follower stats',
      'save_tracking_data': 'Saving tracking data',
      'terminate_app': 'Terminating app',
      
      // Generic patterns for job steps
      'creating_post_1': 'Creating post 1',
      'creating_post_2': 'Creating post 2',
      'starting_automation': 'Starting automation...',
      'executing': 'Processing automation',
      'pending': 'Initializing...',
      'completed': 'Automation completed',
      'failed': 'Automation failed',
      'error': 'Error occurred'
    }
    
    // Check for exact matches first
    if (checkpointMap[checkpoint]) {
      return checkpointMap[checkpoint]
    }
    
    // Check for pattern matches
    if (checkpoint.includes('creating_post_')) {
      const postNum = checkpoint.split('_').pop()
      return `Creating post ${postNum}`
    }
    
    // Fallback to original checkpoint name with cleanup
    return checkpoint.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const getCurrentAction = (device: RunningDevice) => {
    // Use real-time action from WebSocket if available
    const realTimeProgress = deviceProgress[device.id]
    console.log(`🔍 getCurrentAction for device ${device.id}:`, realTimeProgress)
    console.log(`🔍 All deviceProgress keys:`, Object.keys(deviceProgress))
    console.log(`🔍 All deviceProgress data:`, deviceProgress)
    
    if (realTimeProgress && realTimeProgress.currentAction) {
      const mappedAction = mapCheckpointToAction(realTimeProgress.currentAction)
      console.log(`✅ Using real-time action: ${realTimeProgress.currentAction} → ${mappedAction}`)
      return mappedAction
    }
    
    console.log(`⚠️ No real-time data for device ${device.id}, using fallback`)
    console.log(`⚠️ realTimeProgress exists:`, !!realTimeProgress)
    console.log(`⚠️ realTimeProgress.currentAction:`, realTimeProgress?.currentAction)
    
    // Fallback to progress-based actions with clean text
    if (device.status === "running") {
      const progress = getProgressValue(device)
      if (progress < 8) return "Initializing automation..."
      else if (progress < 15) return "Launching Threads App"
      else if (progress < 23) return "Navigating to home feed"
      else if (progress < 31) return "Opening create post"
      else if (progress < 38) return "Entering text content"
      else if (progress < 46) return "Adding media files"
      else if (progress < 54) return "Publishing the post"
      else if (progress < 62) return "Handling popups"
      else if (progress < 69) return "Verifying post success"
      else if (progress < 77) return "Returning to home"
      else if (progress < 85) return "Navigating to profile"
      else if (progress < 92) return "Extracting follower stats"
      else if (progress < 100) return "Saving tracking data"
      else return "Terminating app"
    } else if (device.status === "stopped") {
      return device.lastAction || "Automation stopped"
    } else if (device.status === "paused") {
      return "Automation paused"
    } else if (device.status === "error") {
      return "Error occurred - check logs"
    } else {
      return device.currentStep || "Device idle"
    }
  }

  // Calculate stats
  const runningCount = devices.filter(d => d.status === "running").length
  const pausedCount = devices.filter(d => d.status === "paused").length
  const stoppedCount = devices.filter(d => d.status === "stopped").length
  const errorCount = devices.filter(d => d.status === "error").length


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
                    <PlayIcon className="w-6 h-6 text-black" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold text-white tracking-tight">Running Devices</h1>
                    <p className="text-gray-300 text-lg mt-1">Monitor and control your automation devices</p>
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
                <Button 
                  onClick={() => refetch()}
                  disabled={isLoading}
                  className="bg-white text-black hover:bg-gray-100 border-0 shadow-2xl rounded-2xl px-6 py-3 font-semibold transition-all duration-300 hover:scale-105"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
            
            {/* Search Bar and Platform Switcher - Integrated into header */}
            <div className="mt-8">
              <div className="flex items-center justify-between">
                {/* Search */}
                <div className="flex-1 max-w-md">
                  <GlobalSearchBar placeholder="Search running devices..." />
                </div>

                {/* Right side */}
                <div className="flex items-center space-x-4">
                  <button 
                    onClick={() => {
                      console.log('🧪 Manual test - setting device progress...')
                      const runningDevice = allDevices.find(d => d.status === "running")
                      const testDeviceId = runningDevice?.id || "device-1758399156"
                      console.log('🧪 Testing with device:', testDeviceId)
                      setDeviceProgress(prev => ({
                        ...prev,
                        [testDeviceId]: {
                          progress: 75,
                          currentAction: "manual_test_checkpoint",
                          checkpoint: 9,
                          timestamp: Date.now()
                        }
                      }))
                    }}
                    className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                  >
                    Test UI
                  </button>
                  <PlatformSwitch />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Enhanced Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-green-50 to-emerald-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <div className="text-green-600 text-xl font-bold">▶</div>
                </div>
                <div className="text-3xl font-bold text-green-600">{runningCount}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Running</div>
                <div className="text-sm text-gray-500">Active automations</div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-50 to-amber-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <div className="text-yellow-600 text-xl font-bold">⦀⦀</div>
                </div>
                <div className="text-3xl font-bold text-yellow-600">{pausedCount}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Paused</div>
                <div className="text-sm text-gray-500">Temporarily stopped</div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-slate-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <div className="text-gray-600 text-xl font-bold">■</div>
                </div>
                <div className="text-3xl font-bold text-gray-600">{stoppedCount}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Stopped</div>
                <div className="text-sm text-gray-500">Idle devices</div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100">
            <div className="absolute inset-0 bg-gradient-to-br from-red-50 to-rose-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-red-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <div className="text-red-600 text-xl font-bold">⚠</div>
                </div>
                <div className="text-3xl font-bold text-red-600">{errorCount}</div>
              </div>
              <div className="space-y-1">
                <div className="font-semibold text-gray-900">Errors</div>
                <div className="text-sm text-gray-500">Need attention</div>
              </div>
            </div>
          </div>
        </div>

        {/* Premium Device Cards */}
        <div className="space-y-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center space-y-4">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-gray-200 rounded-full animate-spin border-t-black mx-auto"></div>
                </div>
                <div className="space-y-2">
                  <div className="text-lg font-semibold text-gray-900">Loading devices...</div>
                  <div className="text-sm text-gray-500">Fetching latest device status</div>
                </div>
              </div>
            </div>
          ) : devices.length === 0 ? (
            <div className="text-center py-20">
              <div className="relative">
                <div className="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl flex items-center justify-center mb-6 mx-auto shadow-lg">
                  <Settings className="w-8 h-8" />
                </div>
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-yellow-800">!</span>
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">No devices found</h3>
              <p className="text-gray-500 mb-8 max-w-md mx-auto">
                Connect your automation devices to get started with intelligent social media management
              </p>
              <Button 
                onClick={() => setIsAddDeviceDialogOpen(true)}
                className="bg-black text-white hover:bg-gray-800 rounded-2xl px-8 py-3 font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
              >
                Add Your First Device
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              {devices.map((device) => (
                <div 
                  key={`${device.id}-${deviceProgress[device.id]?.timestamp || 0}`} 
                  className="group relative bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 overflow-hidden"
                >
                  {/* Status Indicator Strip */}
                  <div className={`absolute top-0 left-0 right-0 h-1 ${
                    device.status === "running" 
                      ? "bg-gradient-to-r from-green-400 to-emerald-500" 
                      : device.status === "error"
                      ? "bg-gradient-to-r from-red-400 to-rose-500"
                      : device.status === "paused"
                      ? "bg-gradient-to-r from-yellow-400 to-amber-500"
                      : "bg-gradient-to-r from-gray-300 to-gray-400"
                  }`}></div>

                  <div className="p-8">
                    {/* Device Header */}
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex items-center space-x-4">
                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg ${
                          device.status === "running" 
                            ? "bg-green-100 text-green-600" 
                            : device.status === "error"
                            ? "bg-red-100 text-red-600"
                            : device.status === "paused"
                            ? "bg-yellow-100 text-yellow-600"
                            : "bg-gray-100 text-gray-600"
                        }`}>
                          <Smartphone className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 mb-1">{device.name}</h3>
                          <div className="flex items-center space-x-3">
                            <span className="text-sm text-gray-500">ID: {device.id}</span>
                            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
                            <span className="text-sm text-gray-500">{device.accounts.length} accounts</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className={`px-4 py-2 rounded-full text-sm font-semibold shadow-sm ${
                        device.status === "running" 
                          ? "bg-green-100 text-green-800 border border-green-200" 
                          : device.status === "error"
                          ? "bg-red-100 text-red-800 border border-red-200"
                          : device.status === "paused"
                          ? "bg-yellow-100 text-yellow-800 border border-yellow-200"
                          : "bg-gray-100 text-gray-800 border border-gray-200"
                      }`}>
                        {device.status === "running" && (
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span>Running</span>
                          </div>
                        )}
                        {device.status === "stopped" && "Stopped"}
                        {device.status === "paused" && "Paused"}
                        {device.status === "error" && (
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                            <span>Error</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Enhanced Progress Section */}
                    <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-2xl p-6 mb-6 border border-gray-100">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-bold text-gray-900">Automation Progress</h4>
                        <div className="bg-black text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">
                          {getProgressValue(device)}%
                        </div>
                      </div>
                      
                      {/* Sophisticated Progress Bar */}
                      <div className="relative mb-4">
                        <div className="w-full bg-white rounded-full h-4 overflow-hidden shadow-inner border border-gray-200">
                          <div 
                            className="h-full bg-gradient-to-r from-gray-700 via-black to-gray-800 rounded-full transition-all duration-1000 ease-out relative"
                            style={{ width: `${getProgressValue(device)}%` }}
                          >
                            {/* Animated shine effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 animate-pulse"></div>
                            {/* Progress indicator dot */}
                            {getProgressValue(device) > 5 && (
                              <div className="absolute right-1 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-white rounded-full shadow-sm"></div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Real-time Action Status */}
                      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                        <div className="flex items-center space-x-3">
                          {/* Activity Indicator */}
                          <div className="flex space-x-1">
                            {device.status === "running" ? (
                              <>
                                <div className="w-1.5 h-6 bg-black rounded-full animate-pulse"></div>
                                <div className="w-1.5 h-6 bg-gray-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                                <div className="w-1.5 h-6 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                              </>
                            ) : (
                              <>
                                <div className="w-1.5 h-6 bg-gray-200 rounded-full"></div>
                                <div className="w-1.5 h-6 bg-gray-200 rounded-full"></div>
                                <div className="w-1.5 h-6 bg-gray-200 rounded-full"></div>
                              </>
                            )}
                          </div>
                          
                          <div className="flex-1">
                            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                              {device.status === "running" ? "Current Action" : device.status === "stopped" ? "Last Action" : "Status"}
                            </div>
                            <div className="font-semibold text-gray-900 leading-tight">
                              {getCurrentAction(device)}
                            </div>
                          </div>
                          
                          {/* Status Dot */}
                          <div className="relative">
                            {device.status === "running" && (
                              <>
                                <div className="w-4 h-4 bg-green-500 rounded-full animate-ping absolute opacity-75"></div>
                                <div className="w-4 h-4 bg-green-600 rounded-full"></div>
                              </>
                            )}
                            {device.status === "stopped" && (
                              <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
                            )}
                            {device.status === "error" && (
                              <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                            )}
                            {device.status === "paused" && (
                              <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Control Buttons */}
                    <MorphingButton
                      device={device}
                      startingDevices={startingDevices}
                      stoppingDevices={stoppingDevices}
                      onStart={handleStart}
                      onPause={handlePause}
                      onStop={handleStop}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modern Error Dialog */}
      <Dialog open={errorDialog.isOpen} onOpenChange={(open) => setErrorDialog(prev => ({ ...prev, isOpen: open }))}>
        <DialogContent className="max-w-lg bg-white rounded-3xl border-0 shadow-2xl">
          <DialogHeader className="pb-6">
            <DialogTitle className="flex items-center gap-3 text-xl font-bold">
              <div className="w-12 h-12 bg-red-100 rounded-2xl flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <div className="text-gray-900">{errorDialog.title}</div>
                <div className="text-sm font-normal text-gray-500 mt-1">Device connection issue detected</div>
              </div>
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-2xl p-4">
              <div className="text-sm text-gray-700">
                <strong className="text-gray-900">Error Details:</strong> {errorDialog.message}
              </div>
            </div>
            
            {errorDialog.showTroubleshooting && (
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
                <h4 className="font-bold text-gray-900 flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Usb className="h-4 w-4 text-blue-600" />
                  </div>
                  Quick Fix Solution
                </h4>
                
                <div className="space-y-4">
                  {[
                    { step: "1", action: "Disconnect USB cable", detail: "Wait 3-5 seconds for reset" },
                    { step: "2", action: "Reconnect USB cable", detail: "Ensure secure connection" },
                    { step: "3", action: "Try starting again", detail: "Fresh connection established" }
                  ].map((item) => (
                    <div key={item.step} className="flex items-start gap-4 p-3 bg-white rounded-xl shadow-sm">
                      <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        {item.step}
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{item.action}</div>
                        <div className="text-sm text-gray-600 mt-1">{item.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 p-4 bg-white rounded-xl border border-blue-200">
                  <div className="text-sm text-gray-700">
                    <strong className="text-gray-900">Why this works:</strong> USB connections can become corrupted. 
                    Disconnecting and reconnecting refreshes the connection between your Mac and iPhone.
                  </div>
                </div>
              </div>
            )}
            
            <div className="bg-gray-50 rounded-2xl p-4">
              <div className="font-semibold text-gray-900 mb-3">Additional troubleshooting:</div>
              <ul className="space-y-2 text-sm text-gray-600">
                {[
                  "Ensure iPhone is unlocked and trusted",
                  "Check for 'Trust This Computer' popup on iPhone", 
                  "Try a different USB cable if available",
                  "Restart the Appium server if issues persist"
                ].map((tip, index) => (
                  <li key={index} className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        
          <div className="flex gap-3 pt-6">
            <Button 
              variant="outline" 
              onClick={() => setErrorDialog(prev => ({ ...prev, isOpen: false }))}
              className="flex-1 h-12 rounded-2xl border-2 border-gray-200 hover:border-gray-300 font-semibold"
            >
              Close
            </Button>
            {errorDialog.deviceId && (
              <Button 
                onClick={() => {
                  setErrorDialog(prev => ({ ...prev, isOpen: false }))
                  handleStart(errorDialog.deviceId!)
                }}
                className="flex-1 h-12 bg-black text-white hover:bg-gray-800 rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Device Dialog */}
      <AddDeviceDialog 
        open={isAddDeviceDialogOpen}
        onOpenChange={setIsAddDeviceDialogOpen}
        onDeviceAdded={() => {
          refetch() // Refresh the devices list
        }}
      />
    </div>
  )

  return (
    <LicenseBlocker action="access running devices" platform="instagram" children={children} />
  )
}