/**
 * License-Aware Storage Service
 * 
 * This service ensures all data is isolated by license key and stored
 * on the server for sharing across devices. Uses API calls for data
 * persistence with localStorage as fallback.
 */

import { Device, Template } from '@/lib/types'
import { modelsAPI, Model } from '@/lib/api/models'
import { accountsAPI, Account, AccountCreate, AccountUpdate } from '@/lib/api/accounts'
import { templatesAPI, Template as APITemplate, TemplateCreate, TemplateUpdate } from '@/lib/api/templates'
import { warmupAPI, WarmupTemplate, WarmupTemplateCreate, WarmupTemplateUpdate } from '@/lib/api/warmup'
import { getLicenseContext } from '@/lib/services/license-api-service'

// Best-effort sync of a single account to local backend so backend has container/device mapping
async function syncAccountToLocalBackend(acc: any): Promise<void> {
  try {
    const payload = {
      id: acc.id,
      device_id: String(acc.device_id || acc.device || ''),
      username: acc.threads_username || acc.instagram_username || (acc as any).username || '',
      container_number: String(acc.container_number || ''),
      platform: acc.platform || 'threads',
      account_phase: acc.account_phase || 'posting', // Include the account phase
    }
    // Fire-and-forget
    fetch('http://localhost:8000/api/v1/accounts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).catch(() => {})
  } catch {
    // ignore
  }
}

// Storage keys (will be prefixed with license key)
const STORAGE_KEYS = {
  ACCOUNTS: 'savedAccounts',
  DEVICES: 'savedDevices', 
  TEMPLATES: 'templates',
  DEVICE_TEMPLATES: 'deviceTemplates',
  // New: separate mapping for warmup template assignments per device
  DEVICE_WARMUP_TEMPLATES: 'deviceWarmupTemplates',
  ACCOUNT_DEVICES: 'accountDevices',
  // New: account phases map (accountId -> 'warmup' | 'posting')
  ACCOUNT_PHASES: 'accountPhases',
  MODELS: 'savedModels'
} as const

// Account interface for local storage
export interface LocalAccount {
  id: string
  platform: "instagram" | "threads" | "both"
  instagram_username?: string
  threads_username?: string
  authType?: string
  email?: string
  twoFactorCode?: string
  password?: string
  model?: string
  device?: string
  notes?: string
  status: string
  warmup_phase: string
  followers_count: number | null
  created_at: string
  updated_at: string
  device_id?: string
  container_number?: string
  account_phase?: "warmup" | "posting" // Add account phase field
}

// Device interface for local storage
export interface LocalDevice {
  id: number
  name: string
  udid: string
  ios_version: string
  model: string
  appium_port: number
  wda_port: number
  mjpeg_port: number
  wda_bundle_id?: string
  jailbroken: boolean
  container_number?: string
  status: 'active' | 'offline' | 'error'
  last_seen: string
  created_at: string
  updated_at: string
}

// Template interface for local storage
export interface LocalTemplate {
  id: string
  name: string
  platform: "threads" | "instagram"
  captionsFile?: string
  captionsFileContent?: string // Base64 encoded file content
  photosPostsPerDay: number
  photosFolder?: string
  textPostsPerDay: number
  textPostsFile?: string
  textPostsFileContent?: string // Base64 encoded file content
  followsPerDay: number
  likesPerDay: number
  scrollingTimeMinutes: number
  postingIntervalMinutes: number
  createdAt: string
  updatedAt: string
}

// Warmup template interface for local storage
export interface LocalWarmupTemplate {
  id: string
  name: string
  platform: "threads" | "instagram"
  description?: string
  days: Array<{
    day: number
    scrollTime: number
    likes: number
    follows: number
    comments?: number
    stories?: number
    posts?: number
  }>
  createdAt: string
  updatedAt: string
}

// Model interface for local storage (keeping for backward compatibility)
export interface LocalModel {
  id: string
  name: string
  profilePhoto?: string
  createdAt: string
  updatedAt: string
}

// Log interfaces for local storage
export interface LogEntry {
  id: string
  timestamp: string
  level: "info" | "warning" | "error" | "success"
  message: string
  device: string
}

export interface DayLog {
  date: string
  device: string
  entries: LogEntry[]
  status: "running" | "stopped" | "error"
  startTime?: string
  endTime?: string
}

class LicenseAwareStorageService {
  private currentLicenseKey: string | null = null

  // Initialize with current license key
  initialize(licenseKey: string) {
    this.currentLicenseKey = licenseKey
    console.log("🔐 License-aware storage initialized with key:", licenseKey)
  }

  // Get current license key
  getCurrentLicenseKey(): string | null {
    return this.currentLicenseKey
  }

  // Get license-prefixed key
  private getLicenseKey(key: string): string {
    if (!this.currentLicenseKey) {
      console.warn("⚠️ No license key set, using fallback key")
      return key
    }
    return `${this.currentLicenseKey}_${key}`
  }

  // Generic storage methods
  private getItem<T>(key: string): T | null {
    try {
      const licenseKey = this.getLicenseKey(key)
      const item = localStorage.getItem(licenseKey)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error(`Failed to parse ${key} from localStorage:`, error)
      return null
    }
  }

  private setItem<T>(key: string, value: T): void {
    try {
      const licenseKey = this.getLicenseKey(key)
      localStorage.setItem(licenseKey, JSON.stringify(value))
    } catch (error) {
      console.error(`Failed to save ${key} to localStorage:`, error)
    }
  }

  // Account management - localStorage-first approach
  async getAccounts(): Promise<LocalAccount[]> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('⚠️ No license context available')
      return []
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_accounts_${licenseKey}` // Consistent storage key
    
    console.log('📱 ACCOUNTS - Loading from localStorage...')
    
    const storedAccounts = this.getItem<LocalAccount[]>(storageKey) || []
    console.log(`✅ ACCOUNTS - Loaded ${storedAccounts.length} accounts from localStorage`)
    
    return storedAccounts
  }

  async saveAccounts(accounts: LocalAccount[]): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('⚠️ No license context available for saving accounts')
      return
    }
    
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.ACCOUNTS}`
    
    // Just save to localStorage - database operations are handled by individual methods
    this.setItem(storageKey, accounts)
    console.log(`💾 ACCOUNTS - Cached ${accounts.length} accounts in localStorage`)
  }

  async addAccount(account: LocalAccount): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_accounts_${licenseKey}` // Consistent storage key
    
    console.log('💾 ACCOUNTS - Saving to localStorage...')
    
    const accounts = this.getItem<LocalAccount[]>(storageKey) || []
    
    if (!account.id) {
      account.id = `account_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    
    if (!account.created_at) {
      account.created_at = new Date().toISOString()
    }
    if (!account.updated_at) {
      account.updated_at = new Date().toISOString()
    }
    
    accounts.push(account)
    this.setItem(storageKey, accounts)
    
    console.log(`✅ ACCOUNTS - Saved account "${account.platform === 'instagram' ? account.instagram_username : account.threads_username}" to localStorage (${accounts.length} total)`)
    // Also sync to local backend (best-effort)
    syncAccountToLocalBackend(account)
  }

  async updateAccount(accountId: string, updates: Partial<LocalAccount>): Promise<void> {
    console.log('🔄 ACCOUNTS - Starting update process for account:', accountId)
    console.log('🔄 ACCOUNTS - Updates to apply:', updates)
    
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_accounts_${licenseKey}` // Match the key used in getAccounts
    
    console.log('🔄 ACCOUNTS - Using storage key:', storageKey)
    
    try {
      // Try API first - but only if accountId is a valid number (API accounts)
      const numericId = parseInt(accountId)
      if (!isNaN(numericId) && numericId.toString() === accountId) {
        console.log('📡 ACCOUNTS - Attempting API update for numeric ID:', numericId)
        const accountData: AccountUpdate = {
          username: updates.instagram_username || updates.threads_username,
          platform: updates.platform as 'instagram' | 'threads',
          auth_type: updates.authType as '2fa' | 'non-2fa',
          email: updates.email,
          two_factor_code: updates.twoFactorCode,
          password: updates.password,
          model_id: updates.model ? parseInt(updates.model) : undefined,
          device_id: updates.device ? parseInt(updates.device) : undefined,
          notes: updates.notes,
          container_number: updates.container_number ? parseInt(updates.container_number) : undefined,
          account_phase: updates.account_phase as 'warmup' | 'posting' // Include account phase
        }
        
        await accountsAPI.updateAccount(numericId, accountData)
        console.log('✅ ACCOUNTS - Updated via API successfully')
      } else {
        console.log('📱 ACCOUNTS - String ID detected, skipping API (local-only account):', accountId)
      }
      
      // Update license-specific localStorage
      const accounts = this.getItem<LocalAccount[]>(storageKey) || []
      console.log('🔄 ACCOUNTS - Found accounts in storage:', accounts.length)
      console.log('🔄 ACCOUNTS - Looking for account ID:', accountId)
      
      const index = accounts.findIndex(acc => acc.id === accountId)
      console.log('🔄 ACCOUNTS - Account index found:', index)
      
      if (index !== -1) {
        const oldAccount = accounts[index]
        accounts[index] = { 
          ...accounts[index], 
          ...updates, 
          updated_at: new Date().toISOString() 
        }
        console.log('🔄 ACCOUNTS - Account before update:', oldAccount)
        console.log('🔄 ACCOUNTS - Account after update:', accounts[index])
        
        this.setItem(storageKey, accounts)
        console.log('✅ ACCOUNTS - Successfully updated in localStorage')
        // Sync updated record to local backend
        syncAccountToLocalBackend(accounts[index])
      } else {
        console.error('❌ ACCOUNTS - Account not found in localStorage for update')
      }
      
    } catch (error) {
      console.warn('Failed to update account via API, using license-based localStorage fallback:', error)
      // Fallback to license-specific localStorage
      const accounts = this.getItem<LocalAccount[]>(storageKey) || []
      const index = accounts.findIndex(acc => acc.id === accountId)
      if (index !== -1) {
        accounts[index] = { ...accounts[index], ...updates }
        this.setItem(storageKey, accounts)
      }
    }
  }

  async deleteAccount(accountId: string): Promise<void> {
    console.log('🗑️ ACCOUNTS - Starting delete process for account:', accountId)
    
    const licenseContext = getLicenseContext()
    if (!licenseContext?.isValid) {
      console.error('❌ ACCOUNTS - No valid license context available')
      throw new Error('No valid license context available')
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_accounts_${licenseKey}` // Match the key used in getAccounts
    
    let apiSuccess = false
    let apiError: any = null
    
    try {
      // Try API first - but only if accountId is a valid number (API accounts)
      const numericId = parseInt(accountId)
      if (!isNaN(numericId) && numericId.toString() === accountId) {
        console.log('📡 ACCOUNTS - Attempting API delete for numeric ID:', numericId)
        await accountsAPI.deleteAccount(numericId)
        apiSuccess = true
        console.log('✅ ACCOUNTS - Deleted via API successfully')
      } else {
        console.log('📱 ACCOUNTS - String ID detected, skipping API (local-only account):', accountId)
        apiSuccess = false // Skip API for local-only accounts
      }
    } catch (error) {
      apiError = error
      console.warn('⚠️ ACCOUNTS - API delete failed, using localStorage fallback:', {
        error: error,
        message: error instanceof Error ? error.message : 'Unknown error',
        accountId
      })
    }
    
    // Always update localStorage (either after successful API call or as fallback)
    try {
      const accounts = this.getItem<LocalAccount[]>(storageKey) || []
      const originalCount = accounts.length
      const filtered = accounts.filter(acc => acc.id !== accountId)
      
      if (filtered.length === originalCount) {
        console.warn('⚠️ ACCOUNTS - Account not found in localStorage:', accountId)
        // If API failed and account not in localStorage, throw error
        if (!apiSuccess) {
          throw new Error(`Account with ID ${accountId} not found. API error: ${apiError instanceof Error ? apiError.message : 'Unknown API error'}`)
        }
      } else {
        this.setItem(storageKey, filtered)
        console.log('✅ ACCOUNTS - Updated localStorage after delete. Removed 1 account, remaining:', filtered.length)
      }
    } catch (fallbackError) {
      console.error('❌ ACCOUNTS - Failed to delete account in localStorage:', fallbackError)
      
      // If both API and localStorage failed, throw a comprehensive error
      if (!apiSuccess) {
        throw new Error(`Failed to delete account: API error (${apiError instanceof Error ? apiError.message : 'Unknown'}) and localStorage error (${fallbackError instanceof Error ? fallbackError.message : 'Unknown'})`)
      } else {
        // API succeeded but localStorage failed - this is less critical
        console.warn('⚠️ ACCOUNTS - API delete succeeded but localStorage cleanup failed')
      }
    }
    
    console.log('🎉 ACCOUNTS - Delete process completed for account:', accountId)
  }

  // Device management - License-based shared storage
  getDevices(): LocalDevice[] {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return []
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.DEVICES}`
    
    const devices = this.getItem<LocalDevice[]>(storageKey) || []
    console.log('🔍 GET DEVICES - License key:', licenseKey)
    console.log('🔍 GET DEVICES - Storage key:', storageKey)
    console.log('🔍 GET DEVICES - Found devices:', devices)
    
    // Debug: Check all localStorage keys
    const allKeys = Object.keys(localStorage)
    const deviceKeys = allKeys.filter(key => key.includes('savedDevices'))
    console.log('🔍 GET DEVICES - All device keys in localStorage:', deviceKeys)
    deviceKeys.forEach(key => {
      const value = localStorage.getItem(key)
      console.log(`🔍 GET DEVICES - Key ${key}:`, value)
    })
    
        // Fix: If we find devices in the wrong key, move them to the correct key
        const wrongKey = `${licenseKey}_${licenseKey}_savedDevices`
        const wrongDevices = localStorage.getItem(wrongKey)
        if (wrongDevices && devices.length === 0) {
          console.log('🔧 FIXING - Moving devices from wrong key to correct key')
          localStorage.setItem(storageKey, wrongDevices)
          localStorage.removeItem(wrongKey)
          const fixedDevices = this.getItem<LocalDevice[]>(storageKey) || []
          console.log('🔧 FIXED - Devices now in correct key:', fixedDevices)
          return fixedDevices
        }
        
        // Also check for any other double license key patterns
        const allStorageKeys = Object.keys(localStorage)
        const doubleLicenseKeys = allStorageKeys.filter(key => 
          key.includes(`${licenseKey}_${licenseKey}_savedDevices`) && 
          key !== wrongKey
        )
        
        if (doubleLicenseKeys.length > 0 && devices.length === 0) {
          console.log('🔧 FIXING - Found additional double license keys:', doubleLicenseKeys)
          for (const doubleKey of doubleLicenseKeys) {
            const doubleDevices = localStorage.getItem(doubleKey)
            if (doubleDevices) {
              console.log('🔧 FIXING - Moving devices from', doubleKey, 'to correct key')
              localStorage.setItem(storageKey, doubleDevices)
              localStorage.removeItem(doubleKey)
            }
          }
          const fixedDevices = this.getItem<LocalDevice[]>(storageKey) || []
          console.log('🔧 FIXED - Devices now in correct key:', fixedDevices)
          return fixedDevices
        }
    
    return devices
  }

  saveDevices(devices: LocalDevice[]): void {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key - ensure no double license key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.DEVICES}`
    
    // Clean up any existing double license key patterns
    const allStorageKeys = Object.keys(localStorage)
    const doubleLicenseKeys = allStorageKeys.filter(key => 
      key.includes(`${licenseKey}_${licenseKey}_savedDevices`)
    )
    
    if (doubleLicenseKeys.length > 0) {
      console.log('🔧 CLEANUP - Removing double license key patterns:', doubleLicenseKeys)
      doubleLicenseKeys.forEach(key => localStorage.removeItem(key))
    }
    
    this.setItem(storageKey, devices)
  }

  addDevice(device: LocalDevice): void {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key - ensure no double license key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.DEVICES}`
    
    // Clean up any existing double license key patterns
    const allStorageKeys = Object.keys(localStorage)
    const doubleLicenseKeys = allStorageKeys.filter(key => 
      key.includes(`${licenseKey}_${licenseKey}_savedDevices`)
    )
    
    if (doubleLicenseKeys.length > 0) {
      console.log('🔧 CLEANUP - Removing double license key patterns:', doubleLicenseKeys)
      doubleLicenseKeys.forEach(key => localStorage.removeItem(key))
    }
    
    // Get existing devices
    const devices = this.getDevices()
    devices.push(device)
    this.saveDevices(devices)
  }

  updateDevice(deviceId: number, updates: Partial<LocalDevice>): void {
    const devices = this.getDevices()
    const index = devices.findIndex(dev => dev.id === deviceId)
    if (index !== -1) {
      devices[index] = { ...devices[index], ...updates }
      this.saveDevices(devices)
    }
  }

  deleteDevice(deviceId: number): void {
    const devices = this.getDevices()
    const filtered = devices.filter(dev => dev.id !== deviceId)
    this.saveDevices(filtered)
  }

  // Template management - localStorage-first approach
  async getTemplates(): Promise<LocalTemplate[]> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('⚠️ No license context available')
      return []
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_templates_${licenseKey}` // Consistent storage key
    const oldStorageKey = STORAGE_KEYS.TEMPLATES // Old storage key
    
    console.log('📱 TEMPLATES - Loading from localStorage...')
    console.log('🔍 DEBUG - License key:', licenseKey)
    console.log('🔍 DEBUG - Storage key:', storageKey)
    
    // Try license-aware storage first
    let storedTemplates = this.getItem<LocalTemplate[]>(storageKey) || []
    
    // If no templates found in license-aware storage, check old storage key
    if (storedTemplates.length === 0) {
      console.log('📱 TEMPLATES - No templates in license-aware storage, checking old storage key...')
      const oldTemplates = this.getItem<LocalTemplate[]>(oldStorageKey) || []
      if (oldTemplates.length > 0) {
        console.log(`📱 TEMPLATES - Found ${oldTemplates.length} templates in old storage, migrating...`)
        // Migrate to license-aware storage
        this.setItem(storageKey, oldTemplates)
        // Remove from old storage
        localStorage.removeItem(oldStorageKey)
        storedTemplates = oldTemplates
      }
    }
    
    console.log(`✅ TEMPLATES - Loaded ${storedTemplates.length} templates from localStorage`)
    console.log('📱 TEMPLATES - Template details:', storedTemplates.map(t => ({
      id: t.id,
      name: t.name,
      platform: t.platform,
      postingIntervalMinutes: t.postingIntervalMinutes,
      textPostsPerDay: t.textPostsPerDay,
      createdAt: t.createdAt
    })))
    
    return storedTemplates
  }

  async saveTemplates(templates: LocalTemplate[]): Promise<void> {
    try {
      // Get license context
      const licenseContext = getLicenseContext()
      if (!licenseContext) {
        console.warn('Invalid license context for saving templates')
        return
      }
      
      // Get license-specific storage key
      const licenseKey = licenseContext.licenseKey
      const storageKey = `fsn_templates_${licenseKey}`
      
      this.setItem(storageKey, templates)
      console.log(`💾 TEMPLATES - Saved ${templates.length} templates to localStorage`)
    } catch (error) {
      console.error('Failed to save templates:', error)
    }
  }

  async addTemplate(template: LocalTemplate): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_templates_${licenseKey}` // Consistent storage key
    
    console.log('💾 TEMPLATES - Saving to localStorage...')
    console.log('🔍 DEBUG - Template being saved:', template)
    console.log('🔍 DEBUG - postingIntervalMinutes in template:', template.postingIntervalMinutes)
    console.log('🔍 DEBUG - Storage key:', storageKey)
    
    const templates = this.getItem<LocalTemplate[]>(storageKey) || []
    
    if (!template.id) {
      template.id = `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    
    if (!template.createdAt) {
      template.createdAt = new Date().toISOString()
    }
    if (!template.updatedAt) {
      template.updatedAt = new Date().toISOString()
    }
    
    templates.push(template)
    this.setItem(storageKey, templates)
    
    console.log(`✅ TEMPLATES - Saved template "${template.name}" to localStorage (${templates.length} total)`)
    console.log('🔍 DEBUG - All templates after save:', templates.map(t => ({
      id: t.id,
      name: t.name,
      postingIntervalMinutes: t.postingIntervalMinutes
    })))
  }

  async updateTemplate(templateId: string, updates: Partial<LocalTemplate>): Promise<void> {
    try {
      // Try API first
      const templateData: TemplateUpdate = {
        name: updates.name,
        description: updates.name,
        platform: updates.platform,
        settings: {
          captionsFile: updates.captionsFile,
          photosPostsPerDay: updates.photosPostsPerDay,
          photosFolder: updates.photosFolder,
          textPostsPerDay: updates.textPostsPerDay,
          textPostsFile: updates.textPostsFile,
          followsPerDay: updates.followsPerDay,
          likesPerDay: updates.likesPerDay,
          scrollingTimeMinutes: updates.scrollingTimeMinutes
        }
      }
      
      await templatesAPI.updateTemplate(parseInt(templateId), templateData)
      
      // Update localStorage
      const licenseContext = getLicenseContext()
      if (licenseContext?.isValid && licenseContext.licenseKey) {
        const licenseKey = licenseContext.licenseKey as string
        const storageKey = `fsn_templates_${licenseKey}`
        const templates = this.getItem<LocalTemplate[]>(storageKey) || []
        const index = templates.findIndex(t => t.id === templateId)
        if (index !== -1) {
          templates[index] = { 
            ...templates[index], 
            ...updates, 
            updatedAt: new Date().toISOString() 
          }
          this.setItem(storageKey, templates)
        }
      }
      
    } catch (error) {
      console.warn('Failed to update template via API, using localStorage fallback:', error)
      // Fallback to localStorage
      try {
        const licenseContext = getLicenseContext()
        if (licenseContext?.isValid && licenseContext.licenseKey) {
          const licenseKey = licenseContext.licenseKey as string
          const storageKey = `fsn_templates_${licenseKey}`
          const templates = this.getItem<LocalTemplate[]>(storageKey) || []
          const index = templates.findIndex(t => t.id === templateId)
          if (index !== -1) {
            templates[index] = { ...templates[index], ...updates }
            this.setItem(storageKey, templates)
          }
        }
      } catch (fallbackError) {
        console.error('Failed to update template in localStorage:', fallbackError)
      }
    }
  }

  async deleteTemplate(templateId: string): Promise<void> {
    console.log('🗑️ TEMPLATES - Starting delete process for template:', templateId)
    
    let apiSuccess = false
    let apiError: any = null
    
    try {
      // Try API first
      console.log('📡 TEMPLATES - Attempting API delete...')
      await templatesAPI.deleteTemplate(parseInt(templateId))
      apiSuccess = true
      console.log('✅ TEMPLATES - Deleted via API successfully')
    } catch (error) {
      apiError = error
      console.warn('⚠️ TEMPLATES - API delete failed, using localStorage fallback:', {
        error: error,
        message: error instanceof Error ? error.message : 'Unknown error',
        templateId
      })
      // Continue to localStorage fallback
    }
    
    // Always update localStorage (either after successful API call or as fallback)
    const licenseContext = getLicenseContext()
    console.log('🔍 TEMPLATES - License context check:', { 
      hasContext: !!licenseContext, 
      isValid: licenseContext?.isValid,
      licenseKey: licenseContext?.licenseKey ? 'present' : 'missing'
    })
    
    if (licenseContext?.isValid && licenseContext?.licenseKey) {
      try {
        const licenseKey = licenseContext.licenseKey
        const storageKey = `fsn_templates_${licenseKey}`
        const templates = this.getItem<LocalTemplate[]>(storageKey) || []
        const originalCount = templates.length
        const filtered = templates.filter(t => t.id !== templateId)
        
        console.log('📊 TEMPLATES - localStorage operation:', {
          storageKey,
          originalCount,
          filteredCount: filtered.length,
          templateId,
          found: originalCount !== filtered.length
        })
        
        if (filtered.length === originalCount) {
          console.warn('⚠️ TEMPLATES - Template not found in localStorage:', templateId)
          // For warmup templates, this might be normal if they're only stored locally
          if (!apiSuccess) {
            console.warn('⚠️ TEMPLATES - Template not found in API or localStorage, but this might be expected for warmup templates')
            // Don't throw error for warmup templates - they might only exist locally
          }
        } else {
          this.setItem(storageKey, filtered)
          console.log('✅ TEMPLATES - Updated localStorage after delete. Removed 1 template, remaining:', filtered.length)
        }
      } catch (localStorageError) {
        console.error('❌ TEMPLATES - localStorage operation failed:', localStorageError)
        
        // Only throw error if both API and localStorage failed
        if (!apiSuccess) {
          console.error('❌ TEMPLATES - Both API and localStorage failed')
          // For user experience, we'll log the error but not throw it
          // The UI should handle the error gracefully
        }
      }
    } else {
      console.warn('⚠️ TEMPLATES - Invalid license context, trying alternative storage approach')
      
      // Try alternative storage keys as fallback
      try {
        // Try different storage key formats for different template types
        const alternativeKeys = [
          'fsn_templates', // Old regular templates
          'warmupTemplates', // Old warmup templates
          `fsn_warmup_templates_${licenseContext?.licenseKey}`, // Warmup templates with license
          'templates', // Generic templates
        ]
        
        let found = false
        for (const storageKey of alternativeKeys) {
          try {
            const templates = this.getItem<any[]>(storageKey) || []
            const filtered = templates.filter(t => t.id !== templateId)
            
            if (filtered.length < templates.length) {
              this.setItem(storageKey, filtered)
              console.log(`✅ TEMPLATES - Deleted from fallback storage: ${storageKey}`)
              found = true
              break
            }
          } catch (keyError) {
            console.warn(`⚠️ TEMPLATES - Failed to check storage key: ${storageKey}`, keyError)
          }
        }
        
        if (!found && !apiSuccess) {
          console.warn('⚠️ TEMPLATES - Template not found in any storage location')
        }
      } catch (fallbackError) {
        console.error('❌ TEMPLATES - All fallback methods failed:', fallbackError)
        if (!apiSuccess) {
          console.error('❌ TEMPLATES - Complete deletion failure')
          // Log but don't throw - let the UI handle it gracefully
        }
      }
    }
    
    console.log('🎉 TEMPLATES - Delete process completed for template:', templateId)
  }

  // Warmup template management - localStorage-first (mirror Templates page behavior)
  async getWarmupTemplates(): Promise<LocalWarmupTemplate[]> {
    // Primary source: license-aware localStorage (same as Templates)
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('Invalid license context for warmup templates')
      return []
    }

    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_warmup_templates_${licenseKey}`
    const oldStorageKey = 'warmupTemplates' // Legacy key

    let storedTemplates = this.getItem<LocalWarmupTemplate[]>(storageKey) || []
    if (storedTemplates.length === 0) {
      const legacy = this.getItem<LocalWarmupTemplate[]>(oldStorageKey) || []
      if (legacy.length > 0) {
        this.setItem(storageKey, legacy)
        localStorage.removeItem(oldStorageKey)
        storedTemplates = legacy
      }
    }

    return storedTemplates
  }

  async saveWarmupTemplates(templates: LocalWarmupTemplate[]): Promise<void> {
    try {
      // Get license context
      const licenseContext = getLicenseContext()
      if (!licenseContext) {
        console.warn('Invalid license context for saving warmup templates')
        return
      }
      
      // Get license-specific storage key
      const licenseKey = licenseContext.licenseKey
      const storageKey = `fsn_warmup_templates_${licenseKey}`
      
      this.setItem(storageKey, templates)
      console.log(`💾 WARMUP - Saved ${templates.length} warmup templates to localStorage`)
    } catch (error) {
      console.error('Failed to save warmup templates:', error)
    }
  }

  async deleteWarmupTemplate(templateId: string): Promise<void> {
    console.log('🗑️ WARMUP TEMPLATES - Starting delete process for template:', templateId)
    
    const licenseContext = getLicenseContext()
    console.log('🔍 WARMUP TEMPLATES - License context check:', { 
      hasContext: !!licenseContext, 
      isValid: licenseContext?.isValid,
      licenseKey: licenseContext?.licenseKey ? 'present' : 'missing'
    })
    
    if (licenseContext?.isValid && licenseContext?.licenseKey) {
      try {
        const licenseKey = licenseContext.licenseKey
        const storageKey = `fsn_warmup_templates_${licenseKey}`
        const templates = this.getItem<LocalWarmupTemplate[]>(storageKey) || []
        const originalCount = templates.length
        const filtered = templates.filter(t => t.id !== templateId)
        
        console.log('📊 WARMUP TEMPLATES - localStorage operation:', {
          storageKey,
          originalCount,
          filteredCount: filtered.length,
          templateId,
          found: originalCount !== filtered.length
        })
        
        if (filtered.length === originalCount) {
          console.warn('⚠️ WARMUP TEMPLATES - Template not found in localStorage:', templateId)
          throw new Error(`Warmup template with ID ${templateId} not found`)
        } else {
          this.setItem(storageKey, filtered)
          console.log('✅ WARMUP TEMPLATES - Updated localStorage after delete. Removed 1 template, remaining:', filtered.length)
        }
      } catch (localStorageError) {
        console.error('❌ WARMUP TEMPLATES - localStorage operation failed:', localStorageError)
        throw localStorageError
      }
    } else {
      console.warn('⚠️ WARMUP TEMPLATES - Invalid license context, trying fallback storage')
      
      // Try the old storage key format
      try {
        const oldStorageKey = 'warmupTemplates'
        const templates = this.getItem<LocalWarmupTemplate[]>(oldStorageKey) || []
        const filtered = templates.filter(t => t.id !== templateId)
        
        if (filtered.length < templates.length) {
          this.setItem(oldStorageKey, filtered)
          console.log('✅ WARMUP TEMPLATES - Deleted from fallback storage')
        } else {
          throw new Error(`Warmup template with ID ${templateId} not found in fallback storage`)
        }
      } catch (fallbackError) {
        console.error('❌ WARMUP TEMPLATES - All storage methods failed:', fallbackError)
        throw new Error(`Failed to delete warmup template: ${fallbackError instanceof Error ? fallbackError.message : 'Unknown error'}`)
      }
    }
    
    // Ensure deletion from both storage locations to prevent reappearance on refresh
    try {
      const licenseKey = getLicenseContext()?.licenseKey
      if (licenseKey) {
        const licenseKeyStorage = `fsn_warmup_templates_${licenseKey}`
        const arr1 = this.getItem<LocalWarmupTemplate[]>(licenseKeyStorage) || []
        const arr1f = arr1.filter(t => t.id !== templateId)
        if (arr1f.length !== arr1.length) this.setItem(licenseKeyStorage, arr1f)
      }
      const legacyArr = this.getItem<LocalWarmupTemplate[]>('warmupTemplates') || []
      const legacyF = legacyArr.filter(t => t.id !== templateId)
      if (legacyF.length !== legacyArr.length) this.setItem('warmupTemplates', legacyF)
    } catch {}

    console.log('🎉 WARMUP TEMPLATES - Delete process completed for template:', templateId)
  }

  async addWarmupTemplate(template: LocalWarmupTemplate): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available for warmup template save')
      return
    }

    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_warmup_templates_${licenseKey}`

    // Ensure id and timestamps (mirror Templates save behavior)
    const toSave: LocalWarmupTemplate = { ...template }
    if (!toSave.id) {
      toSave.id = `warmup_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    if (!toSave.createdAt) {
      toSave.createdAt = new Date().toISOString()
    }
    toSave.updatedAt = new Date().toISOString()

    const templates = this.getItem<LocalWarmupTemplate[]>(storageKey) || []
    templates.push(toSave)
    this.setItem(storageKey, templates)

    console.log(`✅ WARMUP - Saved template "${toSave.name}" to localStorage (${templates.length} total)`) 

    // Background server sync disabled to prevent duplicates
  }

  async updateWarmupTemplate(templateId: string, updates: Partial<LocalWarmupTemplate>): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available for warmup template update')
      return
    }

    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_warmup_templates_${licenseKey}`

    const templates = this.getItem<LocalWarmupTemplate[]>(storageKey) || []
    const index = templates.findIndex(t => t.id === templateId)
    if (index === -1) {
      console.warn('Warmup template not found in storage:', templateId)
      return
    }

    const current = templates[index]
    const updated: LocalWarmupTemplate = {
      ...current,
      ...updates,
      days: updates.days ? updates.days : current.days,
      updatedAt: new Date().toISOString(),
    }

    templates[index] = updated
    this.setItem(storageKey, templates)
    console.log('✅ WARMUP - Updated template in localStorage:', templateId)

    // Best-effort API PUT when ID is numeric
    const isNumericId = /^\d+$/.test(templateId)
    if (isNumericId) {
      try {
        const templateData = {
          name: updated.name,
          platform: updated.platform,
          total_days: updated.days.length,
          days_config: updated.days.map(day => ({
            day_number: day.day,
            scroll_minutes: day.scrollTime,
            likes_count: day.likes,
            follows_count: day.follows,
          })),
        }
        await warmupAPI.updateWarmupTemplate(parseInt(templateId, 10), templateData as any)
      } catch {
        // ignore background sync failure
      }
    }
  }

  // Device template assignments
  getDeviceTemplates(): Record<string, string> {
    return this.getItem<Record<string, string>>(STORAGE_KEYS.DEVICE_TEMPLATES) || {}
  }

  saveDeviceTemplates(assignments: Record<string, string>): void {
    this.setItem(STORAGE_KEYS.DEVICE_TEMPLATES, assignments)
  }

  assignTemplateToDevice(deviceId: string, templateId: string): void {
    const assignments = this.getDeviceTemplates()
    assignments[deviceId] = templateId
    this.saveDeviceTemplates(assignments)
  }

  removeTemplateFromDevice(deviceId: string): void {
    const assignments = this.getDeviceTemplates()
    delete assignments[deviceId]
    this.saveDeviceTemplates(assignments)
  }

  // Device warmup template assignments (separate map)
  getDeviceWarmupTemplates(): Record<string, string> {
    return this.getItem<Record<string, string>>(STORAGE_KEYS.DEVICE_WARMUP_TEMPLATES) || {}
  }

  saveDeviceWarmupTemplates(assignments: Record<string, string>): void {
    this.setItem(STORAGE_KEYS.DEVICE_WARMUP_TEMPLATES, assignments)
  }

  assignWarmupTemplateToDevice(deviceId: string, warmupTemplateId: string): void {
    const assignments = this.getDeviceWarmupTemplates()
    assignments[deviceId] = warmupTemplateId
    this.saveDeviceWarmupTemplates(assignments)
  }

  removeWarmupTemplateFromDevice(deviceId: string): void {
    const assignments = this.getDeviceWarmupTemplates()
    delete assignments[deviceId]
    this.saveDeviceWarmupTemplates(assignments)
  }

  // Account device assignments
  getAccountDevices(): Record<string, string> {
    return this.getItem<Record<string, string>>(STORAGE_KEYS.ACCOUNT_DEVICES) || {}
  }

  saveAccountDevices(assignments: Record<string, string>): void {
    this.setItem(STORAGE_KEYS.ACCOUNT_DEVICES, assignments)
  }

  assignDeviceToAccount(accountId: string, deviceId: string): void {
    const assignments = this.getAccountDevices()
    assignments[accountId] = deviceId
    this.saveAccountDevices(assignments)
  }

  removeDeviceFromAccount(accountId: string): void {
    const assignments = this.getAccountDevices()
    delete assignments[accountId]
    this.saveAccountDevices(assignments)
  }

  // Account phase management
  getAccountPhases(): Record<string, 'warmup' | 'posting'> {
    return this.getItem<Record<string, 'warmup' | 'posting'>>(STORAGE_KEYS.ACCOUNT_PHASES) || {}
  }

  setAccountPhase(accountId: string, phase: 'warmup' | 'posting'): void {
    const phases = this.getAccountPhases()
    phases[accountId] = phase
    this.setItem(STORAGE_KEYS.ACCOUNT_PHASES, phases)
    
    // Also update the backend warmup tracking files
    this.updateBackendWarmupPhase(accountId, phase)
  }

  getAccountPhase(accountId: string): 'warmup' | 'posting' {
    const phases = this.getAccountPhases()
    return phases[accountId] || 'posting'
  }

  private updateBackendWarmupPhase(accountId: string, phase: 'warmup' | 'posting'): void {
    try {
      // Get the account to find the username for the backend
      const accounts = this.getAccounts()
      const account = accounts.find(acc => acc.id === accountId)
      if (!account) {
        console.warn('Account not found for phase update:', accountId)
        return
      }

      const username = account.instagram_username || account.threads_username
      if (!username) {
        console.warn('No username found for account:', accountId)
        return
      }

      // Call the backend API to update the warmup phase
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/accounts/update-phase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: accountId,
          username: username,
          phase: phase
        })
      }).then(response => {
        if (response.ok) {
          console.log(`✅ Updated backend phase for ${username} to ${phase}`)
        } else {
          console.warn(`⚠️ Failed to update backend phase for ${username}:`, response.statusText)
        }
      }).catch(error => {
        console.warn(`⚠️ Error updating backend phase for ${username}:`, error)
      })
    } catch (error) {
      console.warn('Error updating backend warmup phase:', error)
    }
  }

  // Model management - API-first with localStorage fallback
  async getModels(): Promise<LocalModel[]> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('⚠️ No license context available')
      return []
    }
    
    // Get license-specific storage key - use consistent format
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_models_${licenseKey}`
    
    console.log('📱 MODELS - Loading from localStorage...')
    
    // Always use localStorage as primary source
    const storedModels = this.getItem<LocalModel[]>(storageKey) || []
    console.log(`✅ MODELS - Loaded ${storedModels.length} models from localStorage`)
    
    return storedModels
  }

  async saveModels(models: LocalModel[]): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('⚠️ No license context available for saving models')
      return
    }
    
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.MODELS}`
    
    try {
      console.log(`🔧 MODELS - Saving ${models.length} models to server...`)
      
      // For each model, try to create/update on server
      for (const model of models) {
        try {
          if (model.id && !isNaN(parseInt(model.id))) {
            // Existing model - update via API (if update endpoint exists)
            console.log(`🔄 MODELS - Updating model ${model.name} on server`)
            // Note: Update endpoint not implemented yet, so we'll create new for now
          }
          
          // Create new model on server
          await modelsAPI.createModel({
            name: model.name,
            profilePhoto: model.profilePhoto || undefined
          })
          console.log(`✅ MODELS - Created model ${model.name} on server`)
          
        } catch (modelError) {
          console.warn(`⚠️ MODELS - Failed to save model ${model.name} to server:`, modelError)
          // Continue with other models
        }
      }
      
      // Cache in localStorage as backup
      this.setItem(storageKey, models)
      console.log(`💾 MODELS - Cached ${models.length} models in localStorage`)
      
    } catch (error) {
      console.error('❌ MODELS - Failed to save models to server:', error)
      
      // Fallback: just save to localStorage
      this.setItem(storageKey, models)
      console.log(`📱 MODELS FALLBACK - Saved ${models.length} models to localStorage only`)
    }
  }

  async addModel(model: LocalModel): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key - use consistent format
    const licenseKey = licenseContext.licenseKey
    const storageKey = `fsn_models_${licenseKey}`
    
    console.log('💾 MODELS - Saving to localStorage...')
    
    // Always save to localStorage (API is just for compatibility)
    const models = this.getItem<LocalModel[]>(storageKey) || []
    
    // Generate unique ID if not provided
    if (!model.id) {
      model.id = `model_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    
    // Set timestamps if not provided
    if (!model.createdAt) {
      model.createdAt = new Date().toISOString()
    }
    if (!model.updatedAt) {
      model.updatedAt = new Date().toISOString()
    }
    
    models.push(model)
    this.setItem(storageKey, models)
    
    console.log(`✅ MODELS - Saved model "${model.name}" to localStorage (${models.length} total)`)
  }

  async updateModel(modelId: string, updates: Partial<LocalModel>): Promise<void> {
    try {
      // Try API first
      await modelsAPI.updateModel(modelId, {
        name: updates.name,
        profilePhoto: updates.profilePhoto
      })
      
      // Update localStorage
      const models = this.getItem<LocalModel[]>(STORAGE_KEYS.MODELS) || []
      const index = models.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models[index] = { 
          ...models[index], 
          ...updates, 
          updatedAt: new Date().toISOString() 
        }
        this.setItem(STORAGE_KEYS.MODELS, models)
      }
      
    } catch (error) {
      console.warn('Failed to update model via API, using localStorage fallback:', error)
      // Fallback to localStorage
      const models = this.getItem<LocalModel[]>(STORAGE_KEYS.MODELS) || []
      const index = models.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models[index] = { ...models[index], ...updates }
        this.setItem(STORAGE_KEYS.MODELS, models)
      }
    }
  }

  async deleteModel(modelId: string): Promise<void> {
    try {
      // Try API first
      await modelsAPI.deleteModel(modelId)
      
      // Update localStorage
      const models = this.getItem<LocalModel[]>(STORAGE_KEYS.MODELS) || []
      const filtered = models.filter(m => m.id !== modelId)
      this.setItem(STORAGE_KEYS.MODELS, filtered)
      
    } catch (error) {
      console.warn('Failed to delete model via API, using localStorage fallback:', error)
      // Fallback to localStorage
      const models = this.getItem<LocalModel[]>(STORAGE_KEYS.MODELS) || []
      const filtered = models.filter(m => m.id !== modelId)
      this.setItem(STORAGE_KEYS.MODELS, filtered)
    }
  }

  // Log management
  getLogForDate(deviceId: string, date: string): DayLog | null {
    const logKey = `log_${deviceId}_${date}`
    return this.getItem<DayLog>(logKey)
  }

  saveLogForDate(deviceId: string, date: string, log: DayLog): void {
    const logKey = `log_${deviceId}_${date}`
    this.setItem(logKey, log)
  }

  addLogEntry(deviceId: string, date: string, entry: LogEntry): void {
    const log = this.getLogForDate(deviceId, date)
    if (log) {
      log.entries.push(entry)
      this.saveLogForDate(deviceId, date, log)
    } else {
      // Create new log for this date
      const newLog: DayLog = {
        date,
        device: deviceId,
        entries: [entry],
        status: "running",
        startTime: new Date().toISOString()
      }
      this.saveLogForDate(deviceId, date, newLog)
    }
  }

  updateLogStatus(deviceId: string, date: string, status: "running" | "stopped" | "error", endTime?: string): void {
    const log = this.getLogForDate(deviceId, date)
    if (log) {
      log.status = status
      if (endTime) {
        log.endTime = endTime
      }
      this.saveLogForDate(deviceId, date, log)
    }
  }

  getAllLogsForDevice(deviceId: string): DayLog[] {
    const logs: DayLog[] = []
    const keys = Object.keys(localStorage)
    const licensePrefix = this.currentLicenseKey ? `${this.currentLicenseKey}_` : ''
    
    keys.forEach(key => {
      if (key.startsWith(`${licensePrefix}log_${deviceId}_`)) {
        const log = this.getItem<DayLog>(key.replace(licensePrefix, ''))
        if (log) {
          logs.push(log)
        }
      }
    })
    
    return logs.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  }

  deleteLogForDate(deviceId: string, date: string): void {
    const logKey = `log_${deviceId}_${date}`
    const licenseKey = this.getLicenseKey(logKey)
    localStorage.removeItem(licenseKey)
  }

  // Utility methods
  clearAllData(): void {
    if (!this.currentLicenseKey) return
    
    const keys = Object.keys(localStorage)
    const licensePrefix = `${this.currentLicenseKey}_`
    
    keys.forEach(key => {
      if (key.startsWith(licensePrefix)) {
        localStorage.removeItem(key)
      }
    })
  }

  async exportData(): Promise<Record<string, any>> {
    return {
      accounts: await this.getAccounts(),
      devices: this.getDevices(),
      templates: await this.getTemplates(),
      deviceTemplates: this.getDeviceTemplates(),
      accountDevices: this.getAccountDevices(),
      models: await this.getModels()
    }
  }

  importData(data: Record<string, any>): void {
    if (data.accounts) this.saveAccounts(data.accounts)
    if (data.devices) this.saveDevices(data.devices)
    if (data.templates) this.saveTemplates(data.templates)
    if (data.deviceTemplates) this.saveDeviceTemplates(data.deviceTemplates)
    if (data.accountDevices) this.saveAccountDevices(data.accountDevices)
    if (data.models) this.saveModels(data.models)
  }

  // Data validation and migration
  async validateAndMigrateData(): Promise<void> {
    // Ensure all required data structures exist
    if (!this.getAccounts()) this.saveAccounts([])
    if (!this.getDevices()) this.saveDevices([])
    const templates = await this.getTemplates()
    if (!templates) this.saveTemplates([])
    if (!this.getDeviceTemplates()) this.saveDeviceTemplates({})
    if (!this.getAccountDevices()) this.saveAccountDevices({})
    const models = await this.getModels()
    if (!models) this.saveModels([])
  }

  // Migration from old global storage to license-aware storage
  async migrateFromGlobalStorage(): Promise<void> {
    if (!this.currentLicenseKey) return

    console.log("🔄 Migrating data from global storage to license-aware storage...")

    // Check if we already have license-aware data
    const [accounts, devices, models] = await Promise.all([
      this.getAccounts(),
      this.getDevices(),
      this.getModels()
    ])
    const hasLicenseData = accounts.length > 0 || devices.length > 0 || models.length > 0
    if (hasLicenseData) {
      console.log("✅ License-aware data already exists, skipping migration")
      return
    }

    // Migrate from global keys
    const globalKeys = Object.values(STORAGE_KEYS)
    let migratedCount = 0

    globalKeys.forEach(key => {
      try {
        const globalData = localStorage.getItem(key)
        if (globalData) {
          const licenseKey = this.getLicenseKey(key)
          localStorage.setItem(licenseKey, globalData)
          migratedCount++
          console.log(`✅ Migrated ${key} to license-aware storage`)
        }
      } catch (error) {
        console.error(`❌ Failed to migrate ${key}:`, error)
      }
    })

    console.log(`🔄 Migration complete: ${migratedCount} data sets migrated`)
  }
}

// Export singleton instance
export const licenseAwareStorageService = new LicenseAwareStorageService()

// Note: validateAndMigrateData() is now called by the LicenseProvider
// after the license key is set, not on import
