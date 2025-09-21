"use client"

import { useState, useMemo, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TrackingFilters } from "@/components/filters/tracking-filters"
import { StatCard } from "@/components/stat-card"
import { LineFollowers } from "@/components/charts/line-followers"
import { BarNewFollowers } from "@/components/charts/bar-new-followers"
import { BarActionsStacked } from "@/components/charts/bar-actions-stacked"
import { LineCompare } from "@/components/charts/line-compare"
import { Sparkline } from "@/components/charts/sparkline"
import { TopGainersTable } from "@/components/tables/top-gainers-table"
import { ExportCsvButton } from "@/components/buttons/export-csv-button"
import { PhaseBadge } from "@/components/phase-badge"
import { HeroCard } from "@/components/hero-card"
import { LicenseBlocker } from "@/components/license-blocker"
import type { TrackingFilters as TrackingFiltersType } from "@/lib/types"
import { TrendingUp, Users, Eye, Activity, BarChart3, RefreshCw, TrendingDown } from "lucide-react"
import { useFollowerTracking, useManualProfileScan, calculateGrowth, type FollowerTrackingEntry } from "@/lib/hooks/use-tracking"


export default function TrackingPage() {
  const [filters, setFilters] = useState<TrackingFiltersType>({
    dateRange: "7",
    phase: "all",
    status: "all",
    useAccountTz: false,
    comparePrevious: false,
  })
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([])

  // Fetch real tracking data
  const { data: trackingResponse, isLoading: trackingLoading, refetch } = useFollowerTracking()
  const manualScanMutation = useManualProfileScan()
  
  // Process tracking data into account summaries
  const accountsData = useMemo(() => {
    if (!trackingResponse?.tracking_data) return []
    
    // Group tracking data by username
    const groupedData: Record<string, FollowerTrackingEntry[]> = {}
    trackingResponse.tracking_data.forEach(entry => {
      if (!groupedData[entry.username]) {
        groupedData[entry.username] = []
      }
      groupedData[entry.username].push(entry)
    })
    
    // Convert to account data format
    return Object.entries(groupedData).map(([username, history]) => {
      const latestEntry = history[history.length - 1]
      const growth = calculateGrowth(history)
      
      return {
        username: username,
        name: latestEntry.name,
        followers: latestEntry.followers_count,
        newFollowers: growth.dailyGrowth,
        avgViews: null, // Not available yet
        actionsPerDay: null, // Not available yet
        timeSeries: history.map(entry => ({
          date: entry.scan_timestamp.split('T')[0], // Extract date
          followers: entry.followers_count,
          likes: null,
          comments: null
        }))
      }
    })
  }, [trackingResponse])
  
  // Calculate summary data
  const summaryData = useMemo(() => {
    if (!trackingResponse?.tracking_data || trackingResponse.tracking_data.length === 0) {
      return {
        totalFollowers: 0,
        newFollowers: 0,
        avgViewsPerPost: 0,
        actionsPerDay: 0,
        followersTimeSeries: [],
        newFollowersTimeSeries: [],
        actionsTimeSeries: []
      }
    }
    
    const latestEntries = accountsData.map(account => 
      trackingResponse.tracking_data.find(entry => entry.username === account.username)
    ).filter(Boolean)
    
    const totalFollowers = latestEntries.reduce((sum, entry) => sum + (entry?.followers_count || 0), 0)
    const newFollowers = accountsData.reduce((sum, account) => sum + (account.newFollowers || 0), 0)
    
    return {
      totalFollowers,
      newFollowers,
      avgViewsPerPost: null,
      actionsPerDay: null,
      followersTimeSeries: [], // Will be populated by charts
      newFollowersTimeSeries: [],
      actionsTimeSeries: []
    }
  }, [trackingResponse, accountsData])
  
  const summaryLoading = trackingLoading
  const accountsLoading = trackingLoading

  const handleFiltersChange = (newFilters: any) => {
    setFilters({ ...filters, ...newFilters })
  }

  const handleAccountSelect = (accountId: string) => {
    if (selectedAccounts.includes(accountId)) {
      setSelectedAccounts(selectedAccounts.filter((id) => id !== accountId))
    } else if (selectedAccounts.length < 5) {
      setSelectedAccounts([...selectedAccounts, accountId])
    }
  }

  const comparisonData = useMemo(() => {
    if (!accountsData || selectedAccounts.length === 0) return []

    const maxLength = Math.max(
      ...selectedAccounts.map((id) => {
        const account = accountsData.find((acc: any) => acc.id === id)
        return account?.timeSeries?.length || 0
      }),
    )

    return Array.from({ length: Math.min(maxLength, 7) }, (_, i) => {
      const dataPoint: any = {
        date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString(),
      }

      selectedAccounts.forEach((accountId) => {
        const account = accountsData.find((acc: any) => acc.id === accountId)
        if (account?.timeSeries?.[i + 7]) {
          dataPoint[accountId] = account.timeSeries[i + 7].followers
        }
      })

      return dataPoint
    })
  }, [accountsData, selectedAccounts])

  const comparisonAccounts = selectedAccounts.map((id) => {
    const account = accountsData?.find((acc: any) => acc.id === id)
    return {
      id,
      username: account?.username || `Account ${id}`,
      color: "#000",
    }
  })

  if (summaryLoading || accountsLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-20 bg-gray-200 rounded-2xl"></div>
          <div className="grid grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-2xl"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Always show data with NA values when no real data is available

  const children = (
    <div className="p-6 space-y-6">
      {/* Hero Card */}
      <HeroCard 
        title="Performance Tracking" 
        subtitle="Monitor your social media growth and automation performance"
        icon={BarChart3}
      >
        <ExportCsvButton />
      </HeroCard>

      {/* Sticky Filters Bar */}
      <TrackingFilters onFiltersChange={handleFiltersChange} />

      {/* Global Growth Section */}
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-900">Global Growth</h2>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Followers"
            value={summaryData?.totalFollowers?.toLocaleString() || "NA"}
            icon={Users}
            trend={{ value: null, isPositive: true }}
          />
          <StatCard
            title="New Followers"
            value={summaryData?.newFollowers?.toLocaleString() || "NA"}
            icon={TrendingUp}
            trend={{ value: null, isPositive: true }}
          />
          <StatCard
            title="Avg Views/Post"
            value={summaryData?.avgViewsPerPost?.toLocaleString() || "NA"}
            icon={Eye}
            trend={{ value: null, isPositive: false }}
          />
          <StatCard
            title="Actions per Day"
            value={summaryData?.actionsPerDay?.toLocaleString() || "NA"}
            icon={Activity}
            trend={{ value: null, isPositive: true }}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <Card className="rounded-2xl shadow-sm border-0 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Total Followers Over Time</h3>
            <LineFollowers data={summaryData?.followersTimeSeries || []} />
          </Card>

          <Card className="rounded-2xl shadow-sm border-0 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">New Followers / Day</h3>
            <BarNewFollowers data={summaryData?.newFollowersTimeSeries || []} />
          </Card>

          <Card className="rounded-2xl shadow-sm border-0 p-6 lg:col-span-2 xl:col-span-1">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Actions Breakdown / Day</h3>
            <BarActionsStacked data={summaryData?.actionsTimeSeries || []} />
          </Card>
        </div>
      </div>

      {/* Per-Account Analysis Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Per-Account Analysis</h2>
          <ExportCsvButton data={accountsData || []} filename="account-performance" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Gainers Table */}
          <TopGainersTable data={accountsData || []} />

          {/* Account Comparison */}
          <Card className="rounded-2xl shadow-sm border-0 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Account Comparison</h3>
            {selectedAccounts.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p>Select up to 5 accounts to compare their growth</p>
                <p className="text-sm mt-1">Click on accounts in the sparklines below</p>
              </div>
            ) : (
              <div>
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">Selected: {selectedAccounts.length}/5 accounts</p>
                  <div className="flex flex-wrap gap-2">
                    {comparisonAccounts.map((account) => (
                      <span
                        key={account.id}
                        className="px-2 py-1 bg-gray-100 rounded-full text-xs cursor-pointer hover:bg-gray-200"
                        onClick={() => handleAccountSelect(account.id)}
                      >
                        {account.username} ×
                      </span>
                    ))}
                  </div>
                </div>
                <LineCompare data={comparisonData} accounts={comparisonAccounts} />
              </div>
            )}
          </Card>
        </div>

        {/* Sparklines Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Account Follower Tracking</h3>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => refetch()}
              disabled={trackingLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${trackingLoading ? 'animate-spin' : ''}`} />
              Refresh Data
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accountsData.length > 0 ? accountsData.map((account: any) => {
              const growth = calculateGrowth(trackingResponse?.tracking_data?.filter(entry => entry.username === account.username) || [])
              const latestScan = trackingResponse?.tracking_data?.find(entry => entry.username === account.username)
              const scanTime = latestScan ? new Date(latestScan.scan_timestamp).toLocaleString() : 'Never'
              
              return (
                <Card key={account.username} className="rounded-2xl shadow-sm border-0 p-4 hover:shadow-md transition-all">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">@{account.username}</CardTitle>
                      <Badge variant={growth.dailyGrowth >= 0 ? "default" : "destructive"} className="text-xs">
                        {growth.dailyGrowth >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {growth.dailyGrowth >= 0 ? '+' : ''}{growth.dailyGrowth}
                      </Badge>
                    </div>
                    <CardDescription className="text-sm text-gray-600">{account.name}</CardDescription>
                  </CardHeader>
                  
                  <CardContent className="pt-2">
                    <div className="space-y-3">
                      {/* Follower Stats */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-gray-500">Current Followers</div>
                          <div className="font-semibold text-lg">{account.followers?.toLocaleString() || "0"}</div>
                        </div>
                        <div>
                          <div className="text-gray-500">Weekly Growth</div>
                          <div className={`font-medium ${growth.weeklyGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {growth.weeklyGrowth >= 0 ? '+' : ''}{growth.weeklyGrowth}
                          </div>
                        </div>
                      </div>
                      
                      {/* Sparkline Chart */}
                      <div className="mb-3">
                        <Sparkline
                          data={
                            account.timeSeries?.map((point: any) => ({
                              date: point.date,
                              value: point.followers,
                            })) || []
                          }
                        />
                      </div>
                      
                      {/* Last Scan Info */}
                      <div className="text-xs text-gray-500 mb-3">
                        Last scan: {scanTime}
                      </div>
                      
                      {/* Manual Scan Button */}
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="w-full"
                        onClick={() => manualScanMutation.mutate("4")} // TODO: Get actual device ID
                        disabled={manualScanMutation.isPending}
                      >
                        {manualScanMutation.isPending ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Scanning...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Scan Now
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            }) : (
              <div className="col-span-full text-center py-12">
                <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Tracking Data Yet</h3>
                <p className="text-gray-600 mb-4">
                  Run some automation jobs to start collecting follower tracking data.
                </p>
                <Button 
                  variant="outline"
                  onClick={() => manualScanMutation.mutate("4")}
                  disabled={manualScanMutation.isPending}
                >
                  {manualScanMutation.isPending ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Start First Scan
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
  
  return <LicenseBlocker>{children}</LicenseBlocker>
}
