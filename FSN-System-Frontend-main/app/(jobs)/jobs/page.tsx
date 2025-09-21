"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  Play, 
  Pause, 
  Square, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  Filter,
  Search,
  Eye,
  Smartphone,
  User
} from "lucide-react"
import { useDevices } from "@/lib/hooks/use-devices"
import { useAccounts } from "@/lib/hooks/use-accounts"

interface Job {
  id: number
  type: string
  status: "pending" | "running" | "completed" | "failed" | "cancelled"
  priority: string
  account_id: number
  device_id: number
  created_at: string
  started_at?: string
  completed_at?: string
  progress?: number
  message?: string
  parameters?: string
}

interface JobDetails {
  id: number
  type: string
  status: string
  progress: number
  message: string
  created_at: string
  started_at?: string
  completed_at?: string
  account: {
    id: number
    username: string
    platform: string
  }
  device: {
    id: number
    name: string
    status: string
  }
  parameters: any
  logs: string[]
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJob, setSelectedJob] = useState<JobDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState("all")
  const [searchTerm, setSearchTerm] = useState("")
  const [ws, setWs] = useState<WebSocket | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const { data: devices } = useDevices()
  const { data: accounts } = useAccounts()

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      const websocket = new WebSocket('ws://localhost:8000/api/v1/jobs/ws')
      
      websocket.onopen = () => {
        console.log('WebSocket connected')
        setWs(websocket)
        wsRef.current = websocket
      }
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'job_update') {
          updateJobStatus(data.job_id, data.status, data.progress, data.message)
        }
      }
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected')
        setWs(null)
        wsRef.current = null
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000)
      }
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // Load jobs on component mount
  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/jobs')
      if (response.ok) {
        const data = await response.json()
        setJobs(data.items || [])
      }
    } catch (error) {
      console.error('Failed to load jobs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const updateJobStatus = (jobId: number, status: string, progress?: number, message?: string) => {
    setJobs(prev => prev.map(job => 
      job.id === jobId 
        ? { 
            ...job, 
            status: status as any, 
            progress: progress || job.progress,
            message: message || job.message
          }
        : job
    ))
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'running':
        return <Play className="w-4 h-4 text-blue-500" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'cancelled':
        return <Square className="w-4 h-4 text-gray-500" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const filteredJobs = jobs.filter(job => {
    const matchesFilter = filter === 'all' || job.status === filter
    const matchesSearch = searchTerm === '' || 
      job.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.message?.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const getAccountInfo = (accountId: number) => {
    return accounts?.data?.items?.find(acc => acc.id === accountId) || null
  }

  const getDeviceInfo = (deviceId: number) => {
    return devices?.data?.items?.find(dev => dev.id === deviceId) || null
  }

  const handleJobAction = async (jobId: number, action: string) => {
    try {
      const response = await fetch(`/api/v1/jobs/${jobId}/${action}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        loadJobs() // Refresh jobs list
      } else {
        console.error(`Failed to ${action} job ${jobId}`)
      }
    } catch (error) {
      console.error(`Error ${action} job:`, error)
    }
  }

  const loadJobDetails = async (jobId: number) => {
    try {
      const response = await fetch(`/api/v1/jobs/${jobId}`)
      if (response.ok) {
        const jobDetails = await response.json()
        setSelectedJob(jobDetails)
      }
    } catch (error) {
      console.error('Failed to load job details:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading jobs...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Job Management</h1>
          <p className="text-muted-foreground">
            Monitor and manage automation jobs in real-time
          </p>
        </div>
        <Button onClick={loadJobs} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Filters and Search */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search jobs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-48">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Jobs</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Jobs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredJobs.map(job => {
          const account = getAccountInfo(job.account_id)
          const device = getDeviceInfo(job.device_id)
          
          return (
            <Card key={job.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {getStatusIcon(job.status)}
                    {job.type.replace(/_/g, ' ').toUpperCase()}
                  </CardTitle>
                  <Badge className={getStatusColor(job.status)}>
                    {job.status}
                  </Badge>
                </div>
                <CardDescription>
                  Created {new Date(job.created_at).toLocaleString()}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Progress Bar */}
                {job.status === 'running' && job.progress !== undefined && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{job.progress}%</span>
                    </div>
                    <Progress value={job.progress} className="h-2" />
                  </div>
                )}

                {/* Account and Device Info */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span>{account?.username || account?.email || 'Unknown Account'}</span>
                    <Badge variant="outline" className="text-xs">
                      {account?.platform || 'unknown'}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4 text-muted-foreground" />
                    <span>{device?.name || 'Unknown Device'}</span>
                    <Badge variant="outline" className="text-xs">
                      {device?.status || 'unknown'}
                    </Badge>
                  </div>
                </div>

                {/* Message */}
                {job.message && (
                  <p className="text-sm text-muted-foreground truncate">
                    {job.message}
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => loadJobDetails(job.id)}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Details
                  </Button>
                  
                  {job.status === 'running' && (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleJobAction(job.id, 'stop')}
                    >
                      <Square className="w-4 h-4 mr-1" />
                      Stop
                    </Button>
                  )}
                  
                  {job.status === 'pending' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleJobAction(job.id, 'start')}
                    >
                      <Play className="w-4 h-4 mr-1" />
                      Start
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredJobs.length === 0 && (
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No jobs found</h3>
          <p className="text-muted-foreground">
            {searchTerm || filter !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'No jobs have been created yet. Execute a template to get started.'
            }
          </p>
        </div>
      )}

      {/* Job Details Modal */}
      <Dialog open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedJob && getStatusIcon(selectedJob.status)}
              Job Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedJob && (
            <div className="space-y-6">
              {/* Job Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Job ID</Label>
                  <p className="text-sm text-muted-foreground">{selectedJob.id}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Type</Label>
                  <p className="text-sm text-muted-foreground">{selectedJob.type}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium">Status</Label>
                  <Badge className={getStatusColor(selectedJob.status)}>
                    {selectedJob.status}
                  </Badge>
                </div>
                <div>
                  <Label className="text-sm font-medium">Progress</Label>
                  <p className="text-sm text-muted-foreground">{selectedJob.progress}%</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Progress</Label>
                <Progress value={selectedJob.progress} className="h-2" />
              </div>

              {/* Account and Device Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Account</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="w-4 h-4" />
                    <span>{selectedJob.account.username}</span>
                    <Badge variant="outline">{selectedJob.account.platform}</Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">Device</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Smartphone className="w-4 h-4" />
                    <span>{selectedJob.device.name}</span>
                    <Badge variant="outline">{selectedJob.device.status}</Badge>
                  </div>
                </div>
              </div>

              {/* Message */}
              {selectedJob.message && (
                <div>
                  <Label className="text-sm font-medium">Message</Label>
                  <p className="text-sm text-muted-foreground mt-1">{selectedJob.message}</p>
                </div>
              )}

              {/* Logs */}
              <div>
                <Label className="text-sm font-medium">Execution Logs</Label>
                <ScrollArea className="h-32 w-full border rounded-md p-3 mt-1">
                  <div className="space-y-1">
                    {selectedJob.logs.map((log, index) => (
                      <p key={index} className="text-xs font-mono text-muted-foreground">
                        {log}
                      </p>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
