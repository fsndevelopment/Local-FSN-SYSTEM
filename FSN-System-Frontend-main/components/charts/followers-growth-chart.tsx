"use client"

import { useState, useEffect, useRef, useMemo, memo } from "react"
import { createPortal } from "react-dom"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Dot, Area, AreaChart, Tooltip } from "recharts"
import { Button } from "@/components/ui/button"
import { ChevronDown, ExternalLink, RefreshCw } from "lucide-react"
import { useQueryClient } from "@tanstack/react-query"
import type { FollowersTrackingSummary, FollowersSeriesPoint } from "@/lib/types"
import { useAccounts } from "@/lib/hooks/use-accounts"
import { useModels } from "@/lib/hooks/use-models"
import { useFollowerTracking } from "@/lib/hooks/use-tracking"
import Link from "next/link"

interface FollowersGrowthChartProps {
  className?: string
  actionsView?: 'daily' | 'weekly'
}


const CustomDot = (props: any) => {
  const { cx, cy, payload, index, dataLength } = props
  // Show dots on first, last, and peak points
  const isImportant = index === 0 || index === dataLength - 1

  if (!isImportant) return null

  return (
    <g>
      <Dot cx={cx} cy={cy} r={3} fill="#000" stroke="#fff" strokeWidth={2} />
      <text x={cx} y={cy - 10} textAnchor="middle" className="text-xs font-medium fill-black">
        {payload.total_followers.toLocaleString()}
      </text>
    </g>
  )
}

// Custom floating tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    const date = new Date(label)
    const formattedDate = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
    
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[140px]">
        <div className="text-xs font-medium text-gray-900 mb-1">{formattedDate}</div>
        <div className="text-sm text-blue-600 font-semibold">
          {data.total_followers?.toLocaleString()} followers
        </div>
        {data.new_followers && (
          <div className="text-xs text-gray-600">
            +{data.new_followers} new
          </div>
        )}
      </div>
    )
  }
  return null
}

const FollowersGrowthChart = memo(function FollowersGrowthChart({ className, actionsView = 'weekly' }: FollowersGrowthChartProps) {
  const [timeRange, setTimeRange] = useState("14d")
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([])
  const [data, setData] = useState<FollowersSeriesPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [showModelsDropdown, setShowModelsDropdown] = useState(false)
  const [showAccountsDropdown, setShowAccountsDropdown] = useState(false)
  
  const modelsDropdownRef = useRef<HTMLDivElement>(null)
  const accountsDropdownRef = useRef<HTMLDivElement>(null)
  const modelsButtonRef = useRef<HTMLButtonElement>(null)
  const accountsButtonRef = useRef<HTMLButtonElement>(null)

  // Get real data from APIs
  const { data: accountsData } = useAccounts()
  const { data: modelsData } = useModels()
  const { data: trackingResponse, refetch: refetchTracking } = useFollowerTracking()
  const queryClient = useQueryClient()

  // Function to clear cached tracking data
  const clearTrackingCache = () => {
    console.log('🧹 DASHBOARD CHART - Clearing tracking cache')
    queryClient.removeQueries({ queryKey: ['tracking'] })
    localStorage.removeItem('tracking_data') // Remove any localStorage cache
    refetchTracking()
  }

  const timeRanges = [
    { label: "7d", value: "7d", days: 7 },
    { label: "14d", value: "14d", days: 14 },
    { label: "30d", value: "30d", days: 30 },
  ]

  // Extract real models and accounts from data
  const realModels = useMemo(() => {
    if (!modelsData?.items) return []
    return modelsData.items
      .map(model => model.name)
      .sort()
  }, [modelsData])

  const realAccounts = useMemo(() => {
    if (!accountsData?.items) return []
    return accountsData.items
      .map(account => `@${account.username}`)
      .sort()
  }, [accountsData])

  // Use real tracking data or generate placeholder data showing zero line
  const chartData = useMemo(() => {
    const selectedRange = timeRanges.find(r => r.value === timeRange)
    const days = selectedRange?.days || 14
    
    // Debug: Log what tracking data we received
    console.log('📊 DASHBOARD CHART - Raw tracking response:', trackingResponse)
    console.log('📊 DASHBOARD CHART - Tracking data exists:', !!trackingResponse?.tracking_data)
    console.log('📊 DASHBOARD CHART - Tracking data length:', trackingResponse?.tracking_data?.length)
    
    // If we have real tracking data, process it
    if (trackingResponse?.tracking_data && trackingResponse.tracking_data.length > 0) {
      console.log('📊 DASHBOARD CHART - Processing real tracking data:', trackingResponse.tracking_data.length, 'entries')
      console.log('📊 DASHBOARD CHART - First few entries:', trackingResponse.tracking_data.slice(0, 3))
      
      // Group tracking data by date and sum followers across all accounts
      const dateMap = new Map<string, number>()
      
      trackingResponse.tracking_data.forEach((entry, index) => {
        // Validate that this is real data, not mock data
        if (!entry.username || !entry.scan_timestamp || typeof entry.followers_count !== 'number') {
          console.warn('📊 DASHBOARD CHART - Invalid tracking entry:', entry)
          return
        }
        
        const date = entry.scan_timestamp.split('T')[0] // Extract date part
        const currentTotal = dateMap.get(date) || 0
        dateMap.set(date, currentTotal + entry.followers_count)
        
        if (index < 5) { // Log first 5 entries for debugging
          console.log(`📊 DASHBOARD CHART - Entry ${index}:`, {
            username: entry.username,
            followers: entry.followers_count,
            date: date,
            timestamp: entry.scan_timestamp,
            isToday: date === new Date().toISOString().split('T')[0]
          })
        }
      })
      
      // Create array of data points for the selected time range
      const realData = []
      const today = new Date()
      
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        const dateString = date.toISOString().split('T')[0]
        
        realData.push({
          date: dateString,
          total_followers: dateMap.get(dateString) || 0,
          new_followers: 0 // TODO: Calculate new followers from previous day
        })
      }
      
      console.log('📊 DASHBOARD CHART - Generated chart data:', realData)
      return realData
    }
    
    // No real data available - generate a flat line at zero to show the chart structure
    console.log('📊 DASHBOARD CHART - No tracking data, showing zero baseline')
    const placeholderData = []
    const today = new Date()
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      
      placeholderData.push({
        date: date.toISOString().split('T')[0],
        total_followers: 0,
        new_followers: 0
      })
    }
    
    return placeholderData
  }, [timeRange, trackingResponse])

  // Set data once when chartData changes
  useEffect(() => {
    setData(chartData)
    setLoading(false)
  }, [chartData])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelsDropdownRef.current && !modelsDropdownRef.current.contains(event.target as Node)) {
        setShowModelsDropdown(false)
      }
      if (accountsDropdownRef.current && !accountsDropdownRef.current.contains(event.target as Node)) {
        setShowAccountsDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const buildTrackingUrl = () => {
    const params = new URLSearchParams()
    if (timeRange !== "14d") params.set("range", timeRange)
    if (selectedModels.length > 0) {
      selectedModels.forEach((model) => params.append("models", model))
    }
    if (selectedAccounts.length > 0) {
      selectedAccounts.forEach((account) => params.append("accounts", account))
    }
    return `/tracking${params.toString() ? `?${params.toString()}` : ""}`
  }

  return (
    <div className={`bg-card rounded-2xl shadow p-6 overflow-visible ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold">Followers growth ({timeRange})</h3>
        <div className="flex items-center space-x-2 relative">
          {/* Time range presets */}
          <div className="flex space-x-1">
            {timeRanges.map((range) => (
              <button
                key={range.value}
                onClick={() => setTimeRange(range.value)}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  timeRange === range.value ? "bg-black text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {range.label}
              </button>
            ))}
            <Button
              onClick={clearTrackingCache}
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs rounded-full ml-2"
              title="Clear cached data and refresh"
            >
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>

          {/* Model selector */}
          <div className="relative" ref={modelsDropdownRef}>
            <Button 
              ref={modelsButtonRef}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setShowModelsDropdown(!showModelsDropdown)
              }}
              variant="outline" 
              size="sm" 
              className="h-7 px-2 text-xs rounded-full border-border bg-transparent"
            >
              Models {selectedModels.length > 0 && `(${selectedModels.length})`} <ChevronDown className="w-3 h-3 ml-1" />
            </Button>
            {showModelsDropdown && typeof window !== 'undefined' && createPortal(
              <div 
                className="fixed bg-white border border-border rounded-lg shadow-xl p-2 min-w-[140px] max-w-[200px]"
                style={{ 
                  zIndex: 999999,
                  top: modelsButtonRef.current ? modelsButtonRef.current.getBoundingClientRect().bottom + 4 : 0,
                  left: modelsButtonRef.current ? modelsButtonRef.current.getBoundingClientRect().left : 0,
                }}
              >
                {realModels.length > 0 ? realModels.map(model => (
                  <div 
                    key={model} 
                    className={`px-2 py-1 text-xs hover:bg-muted rounded cursor-pointer whitespace-nowrap ${
                      selectedModels.includes(model) ? 'bg-blue-100 text-blue-800' : ''
                    }`}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      console.log('Selected model:', model)
                      setSelectedModels(prev => 
                        prev.includes(model) 
                          ? prev.filter(m => m !== model)
                          : [...prev, model]
                      )
                      setShowModelsDropdown(false)
                    }}
                  >
                    {model}
                  </div>
                )) : (
                  <div className="px-2 py-1 text-xs text-muted-foreground">
                    No models available
                  </div>
                )}
              </div>,
              document.body
            )}
          </div>

          {/* Accounts selector */}
          <div className="relative" ref={accountsDropdownRef}>
            <Button 
              ref={accountsButtonRef}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setShowAccountsDropdown(!showAccountsDropdown)
              }}
              variant="outline" 
              size="sm" 
              className="h-7 px-2 text-xs rounded-full border-border bg-transparent"
            >
              Accounts {selectedAccounts.length > 0 && `(${selectedAccounts.length})`} <ChevronDown className="w-3 h-3 ml-1" />
            </Button>
            {showAccountsDropdown && typeof window !== 'undefined' && createPortal(
              <div 
                className="fixed bg-white border border-border rounded-lg shadow-xl p-2 min-w-[140px] max-w-[200px]"
                style={{ 
                  zIndex: 999999,
                  top: accountsButtonRef.current ? accountsButtonRef.current.getBoundingClientRect().bottom + 4 : 0,
                  left: accountsButtonRef.current ? accountsButtonRef.current.getBoundingClientRect().left : 0,
                }}
              >
                {realAccounts.length > 0 ? realAccounts.map(account => (
                  <div 
                    key={account} 
                    className={`px-2 py-1 text-xs hover:bg-muted rounded cursor-pointer whitespace-nowrap ${
                      selectedAccounts.includes(account) ? 'bg-blue-100 text-blue-800' : ''
                    }`}
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      console.log('Selected account:', account)
                      setSelectedAccounts(prev => 
                        prev.includes(account) 
                          ? prev.filter(a => a !== account)
                          : [...prev, account]
                      )
                      setShowAccountsDropdown(false)
                    }}
                  >
                    {account}
                  </div>
                )) : (
                  <div className="px-2 py-1 text-xs text-muted-foreground">
                    No accounts available
                  </div>
                )}
              </div>,
              document.body
            )}
          </div>
        </div>
      </div>

      <div className="h-64 mb-4">
        {loading ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">Loading...</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart 
              key={`chart-${timeRange}`}
              data={data} 
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="50%" stopColor="#3b82f6" stopOpacity={0.4}/>
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: "#6b7280", fontWeight: 500 }}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
                interval="preserveStartEnd"
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: "#6b7280", fontWeight: 500 }}
                tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value.toString()}
                domain={[0, 'dataMax + 100']}
              />
              <Tooltip 
                content={<CustomTooltip />}
                cursor={false}
                allowEscapeViewBox={{ x: false, y: false }}
              />
              <Area
                type="monotone"
                dataKey="total_followers"
                stroke="#3b82f6"
                strokeWidth={3}
                fill="url(#blueGradient)"
                dot={false}
                activeDot={{ 
                  r: 6, 
                  fill: "#3b82f6", 
                  stroke: "#ffffff", 
                  strokeWidth: 2,
                  filter: "drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3))"
                }}
                isAnimationActive={true}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="flex justify-between items-center">
        <div className="text-sm text-muted-foreground">
          {data.length > 0 && (
            <>
              {data[data.length - 1]?.total_followers > 0 ? (
                <>
                  Total: {data[data.length - 1]?.total_followers.toLocaleString()} followers
                  {data.length > 1 && (
                    <span className="ml-2">
                      (+{(data[data.length - 1]?.total_followers - data[0]?.total_followers).toLocaleString()} in{" "}
                      {timeRange})
                    </span>
                  )}
                </>
              ) : (
                <span className="text-gray-500">No tracking data yet - chart shows baseline</span>
              )}
            </>
          )}
        </div>
        <Link href={buildTrackingUrl()}>
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-3 text-xs rounded-full border-border hover:bg-muted/50 bg-transparent"
          >
            Open Tracking <ExternalLink className="w-3 h-3 ml-1" />
          </Button>
        </Link>
      </div>
    </div>
  )
})

export { FollowersGrowthChart }
