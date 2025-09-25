export interface Account {
  id: string
  username: string
  model: string
  followers_count?: number
  warmupDay?: number
  posting_start_at?: string | null
  lastScannedAt?: string
  proxy?: string
  status: "active" | "inactive" | "error" | "pending" | "success"
  timezone?: string
  assignedSchedule?: string
  lastAction?: string
}

export interface Device {
  id: number
  name: string
  udid: string
  ios_version?: string
  model?: string
  appium_port: number
  wda_port: number
  mjpeg_port: number
  wda_bundle_id?: string
  jailbroken: boolean
  status: 'active' | 'offline' | 'error'
  last_seen: string
  proxy_pool_id?: number
  settings?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface TrackingSummary {
  totalFollowers: number
  newFollowers: number
  avgViewsPerPost: number
  actionsPerDay: number
  followersTimeSeries: Array<{
    date: string
    followers: number
  }>
  newFollowersTimeSeries: Array<{
    date: string
    newFollowers: number
  }>
  actionsTimeSeries: Array<{
    date: string
    likes: number
    follows: number
    comments: number
    stories: number
    posts: number
  }>
}

export interface AccountTrackingData {
  id: string
  username: string
  startFollowers: number
  endFollowers: number
  deltaFollowers: number
  avgViews: number
  phase: string
  phaseDay: number
  status: "active" | "paused" | "error"
  timeSeries: Array<{
    date: string
    followers: number
    views: number
    likes: number
    comments: number
  }>
}

export interface TrackingFilters {
  dateRange: string
  from?: string
  to?: string
  modelIds?: string[]
  accountIds?: string[]
  phase?: string
  status?: string
  useAccountTz?: boolean
  comparePrevious?: boolean
}

export interface FollowersSeriesPoint {
  date: string
  total_followers: number
  new_followers: number
}

export interface FollowersTrackingSummary {
  range: { from: string; to: string }
  followers_series: FollowersSeriesPoint[]
  totals: { total_followers: number; new_followers: number }
}

export interface Template {
  id: string
  name: string
  platform: "threads" | "instagram"
  // New simplified structure
  captionsFile?: string // XLSX file for captions (used for photo posts)
  photosPostsPerDay: number // Photos posts per day
  photosFolder?: string // Folder with photos
  textPostsPerDay: number // Text posts per day
  textPostsFile?: string // XLSX file for text posts
  followsPerDay: number
  likesPerDay: number
  scrollingTimeMinutes: number // Scrolling time in minutes
  createdAt: string
  updatedAt: string
}

export interface DeviceWithTemplate extends Device {
  templateId?: string
  template?: Template
  capacityStatus: "safe" | "warning" | "overloaded"
  capacityReason?: string
  assignedAccountsCount: number
}

export interface RunningDevice {
  id: string
  name: string
  status: "running" | "paused" | "stopped" | "error"
  template?: Template
  accounts: Account[]
  lastAction?: string
  pausedAt?: string
  currentStep?: string
  model?: string
  jobStats?: {
    total: number
    running: number
    completed: number
    failed: number
  }
}

export interface WarmupDay {
  day: number
  scrollTime: number // in minutes
  likes: number
  follows: number
}

export interface WarmupTemplate {
  id: string
  name: string
  platform: "threads" | "instagram"
  description?: string
  days: WarmupDay[]
  createdAt: string
  updatedAt: string
}
