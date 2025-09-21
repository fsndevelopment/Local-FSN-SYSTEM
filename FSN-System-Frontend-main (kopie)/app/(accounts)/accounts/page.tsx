"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { HeroCard } from "@/components/hero-card"
import { Plus, RefreshCw, AlertCircle, Users, Edit, Trash2 } from "lucide-react"
import { useAccounts, useAccountStats } from "@/lib/hooks/use-accounts"
import { formatDistanceToNow } from "date-fns"
import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { licenseAwareStorageService, LocalAccount } from "@/lib/services/license-aware-storage-service"
import { ConfirmPopup } from "@/components/ui/unified-popup"
import { LicenseBlocker } from "@/components/license-blocker"
import { usePlatform } from "@/lib/platform"

// Model interface
interface Model {
  id: string
  name: string
  profilePhoto?: string
  created_at: string
  updated_at: string
}

export default function AccountsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedFilter, setSelectedFilter] = useState<string>("all")
  const [currentPlatform] = usePlatform()

  // Mock accounts state for simulation
  const [mockAccounts, setMockAccounts] = useState<any[]>([])
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [accountToDelete, setAccountToDelete] = useState<string | null>(null)
  const [models, setModels] = useState<Model[]>([])
  const [devices, setDevices] = useState<any[]>([])

  // Load models from license-aware storage (now async)
  const loadModels = async () => {
    const savedModels = await licenseAwareStorageService.getModels()
    console.log('🔍 ACCOUNTS PAGE - Loaded models:', savedModels)
    setModels(savedModels)
  }

  // Load devices from license-aware storage (synchronous)
  const loadDevices = () => {
    const savedDevices = licenseAwareStorageService.getDevices()
    console.log('🔍 ACCOUNTS PAGE - Loaded devices:', savedDevices)
    setDevices(savedDevices)
  }

  // Load saved accounts from license-aware storage service (now async)
  useEffect(() => {
    const loadAccounts = async () => {
      const savedAccounts = await licenseAwareStorageService.getAccounts()
      console.log('🔍 ACCOUNTS PAGE - Loaded accounts:', savedAccounts)
      setMockAccounts(savedAccounts)
      await loadModels()
      loadDevices()
    }
    
    loadAccounts()
    
    // Listen for storage changes to refresh when new accounts are added
    const handleStorageChange = () => {
      loadAccounts()
    }
    
    window.addEventListener('storage', handleStorageChange)
    
    // Also refresh when page becomes visible (for same-tab navigation)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        loadAccounts()
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  // This useEffect is now handled in the main useEffect above

  // Listen for URL changes to refresh when coming back from add/edit
  useEffect(() => {
    const refreshParam = searchParams.get('refresh')
    if (refreshParam) {
      // Refresh accounts when refresh parameter is present
      const refreshAccounts = async () => {
        const savedAccounts = await licenseAwareStorageService.getAccounts()
        setMockAccounts(savedAccounts)
        await loadModels()
      }
      refreshAccounts()
    }
  }, [searchParams])

  // Process URL parameters for account editing (removed duplicate account creation)
  // Accounts are now properly saved through the form submission

  // Use real API data for accounts
  const { data: apiAccounts = [], isLoading: accountsLoading, error: accountsError, refetch: refetchAccounts } = useAccounts()
  const { data: stats } = useAccountStats()
  
  // Combine API accounts with local storage accounts for now (migration period)
  // Add null checks to prevent "not iterable" errors
  const allAccounts = [
    ...(Array.isArray(apiAccounts) ? apiAccounts : []),
    ...(Array.isArray(mockAccounts) ? mockAccounts : [])
  ]

  // Handle account deletion
  const handleDeleteAccount = (accountId: string) => {
    setAccountToDelete(accountId)
    setShowDeleteConfirm(true)
  }

  const confirmDeleteAccount = async () => {
    if (accountToDelete) {
      // Delete from license-aware storage service (now async)
      await licenseAwareStorageService.deleteAccount(accountToDelete)
      
      // Update local state
      setMockAccounts(prev => {
        const updatedAccounts = prev.filter(account => account.id !== accountToDelete)
        return updatedAccounts
      })
    }
    setShowDeleteConfirm(false)
    setAccountToDelete(null)
  }

  // Manual refresh function (now async)
  const refreshAccounts = async () => {
    const savedAccounts = await licenseAwareStorageService.getAccounts()
    setMockAccounts(savedAccounts)
    await loadModels()
  }

  // Handle account editing
  const handleEditAccount = (account: any) => {
    // Navigate to edit page with account data as URL params
    const params = new URLSearchParams({
      platform: account.platform,
      username: account.instagram_username || account.threads_username || '',
      status: account.status || '',
      warmup_phase: account.warmup_phase || '',
      edit: 'true',
      id: account.id
    })
    
    router.push(`/accounts/add?${params.toString()}`)
  }

  // Handle filter change
  const handleFilterChange = (filter: string) => {
    setSelectedFilter(filter)
  }

  // Filter accounts based on selected filter and platform
  const filteredAccounts = allAccounts.filter(account => {
    // Add null check for account
    if (!account) return false
    
    // Platform filtering
    if (currentPlatform !== 'all') {
      if (currentPlatform === 'instagram' && account.platform !== 'instagram' && account.platform !== 'both') {
        return false
      }
      if (currentPlatform === 'threads' && account.platform !== 'threads' && account.platform !== 'both') {
        return false
      }
    }
    
    // Status filtering
    switch (selectedFilter) {
      case "posting":
        return account.status === 'active' && account.warmup_phase === 'complete'
      case "warmup":
        return account.warmup_phase && account.warmup_phase !== 'complete'
      case "paused":
        return account.status === 'paused'
      case "error":
        return account.status === 'error'
      case "all":
      default:
        return true
    }
  })

  // API hooks are now defined above

  // Show loading state while data is being fetched
  if (accountsLoading) {
    return (
      <LicenseBlocker action="access account management">
        <div className="space-y-6">
          <HeroCard title="Account Management" subtitle="Loading your accounts..." icon={Users}>
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black"></div>
              <span>Loading...</span>
            </div>
          </HeroCard>
        </div>
      </LicenseBlocker>
    )
  }

  return (
    <LicenseBlocker action="access account management">
      <div className="space-y-6">
      <HeroCard title="Account Management" subtitle="Monitor and manage your Instagram & Threads accounts" icon={Users}>
        <div className="flex space-x-3">
          <Button 
            onClick={() => router.push('/accounts/add')}
            className="bg-black text-white hover:bg-neutral-900 rounded-full px-6"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
          <Button 
            onClick={refreshAccounts}
            variant="outline"
            className="rounded-full px-6"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </HeroCard>

      {/* Clickable Filter Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <button 
          className={`bg-card rounded-2xl shadow p-6 text-left transition-all duration-200 hover:shadow-lg hover:scale-105 ${
            selectedFilter === "all" 
              ? "ring-2 ring-black bg-gray-50" 
              : "hover:bg-gray-50"
          }`}
          onClick={() => handleFilterChange("all")}
        >
          <div className="text-2xl font-bold text-foreground mb-1">
            {allAccounts.length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Total Accounts</div>
          <div className="text-xs text-muted-foreground">All managed accounts</div>
          <div className="text-xs text-blue-600 mt-2 font-medium">Click to view all accounts</div>
        </button>

        <button 
          className={`bg-card rounded-2xl shadow p-6 text-left transition-all duration-200 hover:shadow-lg hover:scale-105 ${
            selectedFilter === "posting" 
              ? "ring-2 ring-black bg-gray-50" 
              : "hover:bg-gray-50"
          }`}
          onClick={() => handleFilterChange("posting")}
        >
          <div className="text-2xl font-bold text-green-600 mb-1">
            {allAccounts.filter(a => a.status === 'active' && a.warmup_phase === 'complete').length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Posting</div>
          <div className="text-xs text-muted-foreground">Active posting phase</div>
          <div className="text-xs text-green-600 mt-2 font-medium">Click to view posting accounts</div>
        </button>

        <button 
          className={`bg-card rounded-2xl shadow p-6 text-left transition-all duration-200 hover:shadow-lg hover:scale-105 ${
            selectedFilter === "warmup" 
              ? "ring-2 ring-black bg-gray-50" 
              : "hover:bg-gray-50"
          }`}
          onClick={() => handleFilterChange("warmup")}
        >
          <div className="text-2xl font-bold text-yellow-600 mb-1">
            {allAccounts.filter(a => a.warmup_phase && a.warmup_phase !== 'complete').length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Warmup</div>
          <div className="text-xs text-muted-foreground">In warmup phase</div>
          <div className="text-xs text-yellow-600 mt-2 font-medium">Click to view warmup accounts</div>
        </button>

        <button 
          className={`bg-card rounded-2xl shadow p-6 text-left transition-all duration-200 hover:shadow-lg hover:scale-105 ${
            selectedFilter === "paused" 
              ? "ring-2 ring-black bg-gray-50" 
              : "hover:bg-gray-50"
          }`}
          onClick={() => handleFilterChange("paused")}
        >
          <div className="text-2xl font-bold text-gray-600 mb-1">
            {allAccounts.filter(a => a.status === 'paused').length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Paused</div>
          <div className="text-xs text-muted-foreground">Temporarily paused</div>
          <div className="text-xs text-gray-600 mt-2 font-medium">Click to view paused accounts</div>
        </button>

        <button 
          className={`bg-card rounded-2xl shadow p-6 text-left transition-all duration-200 hover:shadow-lg hover:scale-105 ${
            selectedFilter === "error" 
              ? "ring-2 ring-black bg-gray-50" 
              : "hover:bg-gray-50"
          }`}
          onClick={() => handleFilterChange("error")}
        >
          <div className="text-2xl font-bold text-red-600 mb-1">
            {allAccounts.filter(a => a.status === 'error').length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Error</div>
          <div className="text-xs text-muted-foreground">Needs attention</div>
          <div className="text-xs text-red-600 mt-2 font-medium">Click to view error accounts</div>
        </button>
      </div>

      {/* Account List */}
      <div className="space-y-4">
        {filteredAccounts.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No accounts found</h3>
            <p className="text-muted-foreground mb-4">
              {selectedFilter === "all" 
                ? "Get started by adding your first account" 
                : `No accounts found for ${selectedFilter} filter`}
            </p>
            <Button onClick={() => router.push('/accounts/add')} className="bg-black text-white hover:bg-neutral-900">
              <Plus className="w-4 h-4 mr-2" />
              Add Account
            </Button>
          </div>
        ) : (
          filteredAccounts.map((account) => (
            <Card key={account.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="relative">
                      {/* Model Profile Picture */}
                      <div className="w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                        {(() => {
                          const assignedModel = findModelByName(account.model || '', models)
                          if (assignedModel?.profilePhoto) {
                            return (
                              <img 
                                src={assignedModel.profilePhoto} 
                                alt={assignedModel.name}
                                className="w-full h-full object-cover"
                              />
                            )
                          } else {
                            // Fallback to first letter of username
                            return (
                              <span className="text-white font-bold text-lg">
                                {account.instagram_username?.charAt(0).toUpperCase() || account.threads_username?.charAt(0).toUpperCase() || 'A'}
                              </span>
                            )
                          }
                        })()}
                      </div>
                      {/* Platform Icon */}
                      <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-white rounded-full border-2 border-white shadow-sm flex items-center justify-center">
                        {(() => {
                          const platformIcon = getPlatformIcon(account.platform)
                          return (
                            <img 
                              src={platformIcon} 
                              alt={account.platform}
                              className="w-4 h-4 object-contain"
                              onError={(e) => {
                                console.error('Failed to load platform icon:', platformIcon)
                                e.currentTarget.style.display = 'none'
                              }}
                            />
                          )
                        })()}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-foreground">
                        {formatPlatform(account.platform, account.instagram_username, account.threads_username)}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>Followers: {account.followers_count ? account.followers_count.toLocaleString() : 'NA'}</span>
                        <span>•</span>
                        <span>Status: {account.status || 'Unknown'}</span>
                        {account.warmup_phase && (
                          <>
                            <span>•</span>
                            <span>Phase: {formatWarmupPhase(account.warmup_phase)}</span>
                          </>
                        )}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-2">
                        {console.log('🔍 ACCOUNT CARD DEBUG - Account:', account)}
                        {console.log('🔍 ACCOUNT CARD DEBUG - Account.model:', account.model)}
                        {console.log('🔍 ACCOUNT CARD DEBUG - Account.password:', account.password)}
                        {console.log('🔍 ACCOUNT CARD DEBUG - Account.device:', account.device)}
                        {console.log('🔍 ACCOUNT CARD DEBUG - Models:', models)}
                        {console.log('🔍 ACCOUNT CARD DEBUG - Devices:', devices)}
                        {account.model && (
                          <>
                            <span>Model: {account.model}</span>
                            <span>•</span>
                          </>
                        )}
                        {account.device && (
                          <>
                            <span>Device: {findDeviceById(account.device, devices)?.name || account.device}</span>
                            <span>•</span>
                          </>
                        )}
                        {account.password && (
                          <span>Password: {account.password}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditAccount(account)}
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteAccount(account.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Error State */}
      {accountsError && (
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">Failed to load accounts</h3>
          <p className="text-muted-foreground mb-4">
            {accountsError.message || "Something went wrong while loading your accounts"}
          </p>
          <Button onClick={() => refetchAccounts()} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      )}

      {/* Delete Confirmation Popup */}
      <ConfirmPopup
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={confirmDeleteAccount}
        title="Delete Account"
        message="Are you sure you want to delete this account? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
      />
      </div>
    </LicenseBlocker>
  )
}

// Helper functions
const formatWarmupPhase = (phase?: string) => {
  switch (phase) {
    case 'phase_1': return 'Phase 1'
    case 'phase_2': return 'Phase 2'
    case 'phase_3': return 'Phase 3'
    case 'complete': return 'Complete'
    default: return 'Unknown'
  }
}

const formatPlatform = (platform: string, instagramUsername?: string, threadsUsername?: string) => {
  switch (platform) {
    case 'instagram':
      return `Instagram: ${instagramUsername || 'N/A'}`
    case 'threads':
      return `Threads: ${threadsUsername || 'N/A'}`
    case 'both':
      return `Instagram & Threads`
    default:
      return platform
  }
}

// Function to find model by name
const findModelByName = (modelName: string, models: Model[]): Model | null => {
  return models.find(model => model.name === modelName) || null
}

// Function to find device by ID
const findDeviceById = (deviceId: string, devices: any[]): any | null => {
  return devices.find(device => device.id.toString() === deviceId) || null
}

// Function to get platform icon
const getPlatformIcon = (platform: string) => {
  switch (platform) {
    case 'instagram':
      return '/instagram.png'
    case 'threads':
      return '/threads.png'
    case 'both':
      return '/instagram.png' // Default to Instagram for both
    default:
      return '/instagram.png'
  }
}