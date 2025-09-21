"use client"

import { useState } from "react"
import Link from "next/link"
import { HeroCard } from "@/components/hero-card"
import { StatusBadge } from "@/components/status-badge"
import { PhaseBadge } from "@/components/phase-badge"
import { WarmupChecklist } from "@/components/warmup-checklist"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { Heart, MessageCircle, Eye, BarChart3, SettingsIcon, User, Scan, ExternalLink } from "lucide-react"
import { scanAccount } from "@/lib/api/endpoints"
import { humanizeDate, getPostingDay } from "@/lib/utils/time"
import type { Account } from "@/lib/types"

// Mock account data with new fields
const accountData: Account & {
  displayName: string
  following: number
  posts: number
  recentPosts: Array<{
    id: string
    caption: string
    views: number
    likes: number
    comments: number
    timestamp: string
  }>
  weeklyViews: number
  weeklyLikes: number
  weeklyComments: number
} = {
  id: "account-1",
  username: "@lifestyle_blogger",
  displayName: "Lifestyle Blogger",
  model: "iPhone 15 Pro",
  followers_count: 12500,
  posting_start_at: "2024-01-15T00:00:00Z",
  lastScannedAt: "2024-01-20T10:30:00Z",
  status: "active",
  proxy: "US-West-01",
  timezone: "America/New_York",
  assignedSchedule: "Daily Mix",
  following: 1200,
  posts: 89,
  weeklyViews: 15600,
  weeklyLikes: 892,
  weeklyComments: 156,
  recentPosts: [
    {
      id: "1",
      caption: "Morning coffee vibes ☕",
      views: 2400,
      likes: 156,
      comments: 23,
      timestamp: "2 hours ago",
    },
    {
      id: "2",
      caption: "Sunset at the beach 🌅",
      views: 3200,
      likes: 289,
      comments: 45,
      timestamp: "1 day ago",
    },
    {
      id: "3",
      caption: "New workout routine!",
      views: 1800,
      likes: 134,
      comments: 18,
      timestamp: "2 days ago",
    },
  ],
}

const tabs = [
  { id: "overview", label: "Overview", icon: User },
  { id: "activity", label: "Activity", icon: BarChart3 },
  { id: "settings", label: "Settings", icon: SettingsIcon },
]


export default function AccountDetailPage({ params }: { params: { id: string } }) {
  const [activeTab, setActiveTab] = useState("overview")
  const [isScanning, setIsScanning] = useState(false)
  const { toast } = useToast()

  const handleScanProfile = async () => {
    setIsScanning(true)
    try {
      await scanAccount(params.id)
      toast({
        title: "Profile scan initiated",
        description: "Account data will be updated shortly.",
      })
      // In a real app, you'd refetch the account data here
    } catch (error) {
      toast({
        title: "Scan failed",
        description: "Unable to scan profile. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <div className="space-y-6">
      <HeroCard title={accountData.username} subtitle={`${accountData.displayName} • ${accountData.model}`} icon={User}>
        <div className="flex items-center space-x-2">
          <PhaseBadge account={accountData} />
          <StatusBadge status={accountData.status}>{accountData.status}</StatusBadge>
        </div>
      </HeroCard>

      {/* Tab Navigation */}
      <div className="flex space-x-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              activeTab === tab.id ? "bg-black text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-card rounded-2xl shadow p-6">
                <div className="text-2xl font-bold text-foreground mb-1">
                  {accountData.followers_count?.toLocaleString()}
                </div>
                <div className="text-sm font-medium text-foreground">Followers</div>
              </div>
              <div className="bg-card rounded-2xl shadow p-6">
                <div className="text-2xl font-bold text-foreground mb-1">
                  {accountData.weeklyViews.toLocaleString()}
                </div>
                <div className="text-sm font-medium text-foreground">7-day Views</div>
              </div>
              <div className="bg-card rounded-2xl shadow p-6">
                <div className="text-2xl font-bold text-foreground mb-1">
                  {accountData.weeklyLikes.toLocaleString()}
                </div>
                <div className="text-sm font-medium text-foreground">7-day Likes</div>
              </div>
              <div className="bg-card rounded-2xl shadow p-6">
                <div className="text-2xl font-bold text-foreground mb-1">{accountData.weeklyComments}</div>
                <div className="text-sm font-medium text-foreground">7-day Comments</div>
              </div>
            </div>

            <div className="bg-card rounded-2xl shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold">Account Phase</h3>
                  <div className="flex items-center space-x-2 mt-2">
                    <PhaseBadge account={accountData} />
                    {accountData.posting_start_at && (
                      <span className="text-sm text-muted-foreground">
                        Posting Day {getPostingDay(accountData.posting_start_at)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Link href={`/tracking?account=${params.id}`}>
                    <Button variant="outline" className="rounded-full px-5 py-2.5 bg-transparent">
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Open Tracking
                      <ExternalLink className="w-3 h-3 ml-2" />
                    </Button>
                  </Link>
                  <Button
                    onClick={handleScanProfile}
                    disabled={isScanning}
                    className="bg-black text-white hover:bg-neutral-900 rounded-full px-5 py-2.5"
                  >
                    <Scan className="w-4 h-4 mr-2" />
                    {isScanning ? "Scanning..." : "Scan Profile"}
                  </Button>
                </div>
              </div>
              {accountData.lastScannedAt && (
                <div className="text-xs text-muted-foreground mt-1">
                  Last scanned: {humanizeDate(accountData.lastScannedAt)}
                </div>
              )}
            </div>

            <div className="bg-card rounded-2xl shadow p-6">
              <h3 className="font-semibold mb-4">Recent Posts</h3>
              <div className="space-y-3">
                {accountData.recentPosts.map((post) => (
                  <div key={post.id} className="p-3 bg-muted/30 rounded-xl">
                    <div className="font-medium text-sm mb-2">{post.caption}</div>
                    <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Eye className="w-3 h-3" />
                        <span>{post.views.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Heart className="w-3 h-3" />
                        <span>{post.likes}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <MessageCircle className="w-3 h-3" />
                        <span>{post.comments}</span>
                      </div>
                      <span>{post.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <WarmupChecklist />
          </div>
        </div>
      )}

      {activeTab === "activity" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-card rounded-2xl shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Activity Timeline</h3>
                <Link href={`/tracking?account=${params.id}`}>
                  <Button variant="outline" size="sm" className="rounded-full bg-transparent">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    View Detailed Charts
                  </Button>
                </Link>
              </div>
              <div className="space-y-4">
                {[
                  { time: "2 hours ago", action: "Posted new story", type: "story" },
                  { time: "4 hours ago", action: "Liked 15 posts", type: "like" },
                  { time: "6 hours ago", action: "Followed 3 accounts", type: "follow" },
                  { time: "8 hours ago", action: "Posted photo", type: "post" },
                  { time: "12 hours ago", action: "Commented on 5 posts", type: "comment" },
                ].map((activity, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-muted/30 rounded-xl">
                    <div className="w-2 h-2 bg-black rounded-full"></div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{activity.action}</div>
                      <div className="text-xs text-muted-foreground">{activity.time}</div>
                    </div>
                    <span className="text-xs bg-muted px-2 py-1 rounded-full">{activity.type}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-card rounded-2xl shadow p-6">
            <h3 className="font-semibold mb-4">Recent Activity</h3>
            <div className="h-32 bg-muted/30 rounded-xl flex items-end justify-center p-4">
              <div className="flex items-end space-x-1">
                {[40, 60, 30, 80, 50, 70, 90].map((height, i) => (
                  <div key={i} className="w-3 bg-black rounded-t" style={{ height: `${height}%` }} />
                ))}
              </div>
            </div>
            <div className="text-center mt-2">
              <Link href={`/tracking?account=${params.id}`}>
                <Button variant="ghost" size="sm" className="text-xs">
                  View full analytics →
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === "settings" && (
        <div className="max-w-2xl">
          <div className="bg-card rounded-2xl shadow p-6">
            <h3 className="font-semibold mb-6">Account Settings</h3>
            <form className="space-y-6">
              {accountData.posting_start_at && (
                <div>
                  <Label>Posting Since</Label>
                  <div className="mt-1 p-3 bg-muted/30 rounded-full text-sm">
                    {humanizeDate(accountData.posting_start_at)} ({getPostingDay(accountData.posting_start_at)} days)
                  </div>
                </div>
              )}

              <div>
                <Label htmlFor="timezone">Timezone</Label>
                <Select defaultValue={accountData.timezone}>
                  <SelectTrigger className="rounded-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="America/New_York">Eastern Time</SelectItem>
                    <SelectItem value="America/Chicago">Central Time</SelectItem>
                    <SelectItem value="America/Denver">Mountain Time</SelectItem>
                    <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="proxy">Proxy Pool</Label>
                <Select defaultValue={accountData.proxy}>
                  <SelectTrigger className="rounded-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="US-West-01">US-West-01</SelectItem>
                    <SelectItem value="US-East-02">US-East-02</SelectItem>
                    <SelectItem value="EU-Central-01">EU-Central-01</SelectItem>
                    <SelectItem value="Asia-Pacific-01">Asia-Pacific-01</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button className="w-full bg-black text-white hover:bg-neutral-900 rounded-full">Save Changes</Button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
