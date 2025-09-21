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

// Storage keys (will be prefixed with license key)
const STORAGE_KEYS = {
  ACCOUNTS: 'savedAccounts',
  DEVICES: 'savedDevices', 
  TEMPLATES: 'templates',
  DEVICE_TEMPLATES: 'deviceTemplates',
  ACCOUNT_DEVICES: 'accountDevices',
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
  }

  async updateAccount(accountId: string, updates: Partial<LocalAccount>): Promise<void> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.ACCOUNTS}`
    
    try {
      // Try API first
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
        container_number: updates.container_number ? parseInt(updates.container_number) : undefined
      }
      
      await accountsAPI.updateAccount(parseInt(accountId), accountData)
      
      // Update license-specific localStorage
      const accounts = this.getItem<LocalAccount[]>(storageKey) || []
      const index = accounts.findIndex(acc => acc.id === accountId)
      if (index !== -1) {
        accounts[index] = { 
          ...accounts[index], 
          ...updates, 
          updated_at: new Date().toISOString() 
        }
        this.setItem(storageKey, accounts)
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
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      console.warn('No license context available')
      return
    }
    
    // Get license-specific storage key
    const licenseKey = licenseContext.licenseKey
    const storageKey = `${licenseKey}_${STORAGE_KEYS.ACCOUNTS}`
    
    try {
      // Try API first
      await accountsAPI.deleteAccount(parseInt(accountId))
      
      // Update license-specific localStorage
      const accounts = this.getItem<LocalAccount[]>(storageKey) || []
      const filtered = accounts.filter(acc => acc.id !== accountId)
      this.setItem(storageKey, filtered)
      
    } catch (error) {
      console.warn('Failed to delete account via API, using license-based localStorage fallback:', error)
      // Fallback to license-specific localStorage
      const accounts = this.getItem<LocalAccount[]>(storageKey) || []
      const filtered = accounts.filter(acc => acc.id !== accountId)
      this.setItem(storageKey, filtered)
    }
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
      if (licenseContext.isValid) {
        const licenseKey = licenseContext.licenseKey
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
        if (licenseContext.isValid) {
          const licenseKey = licenseContext.licenseKey
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
    try {
      // Try API first
      await templatesAPI.deleteTemplate(parseInt(templateId))
      
      // Update localStorage
      const licenseContext = getLicenseContext()
      if (licenseContext.isValid) {
        const licenseKey = licenseContext.licenseKey
        const storageKey = `fsn_templates_${licenseKey}`
        const templates = this.getItem<LocalTemplate[]>(storageKey) || []
        const filtered = templates.filter(t => t.id !== templateId)
        this.setItem(storageKey, filtered)
      }
      
    } catch (error) {
      console.warn('Failed to delete template via API, using localStorage fallback:', error)
      // Fallback to localStorage
      try {
        const licenseContext = getLicenseContext()
        if (licenseContext.isValid) {
          const licenseKey = licenseContext.licenseKey
          const storageKey = `fsn_templates_${licenseKey}`
          const templates = this.getItem<LocalTemplate[]>(storageKey) || []
          const filtered = templates.filter(t => t.id !== templateId)
          this.setItem(storageKey, filtered)
        }
      } catch (fallbackError) {
        console.error('Failed to delete template in localStorage:', fallbackError)
      }
    }
  }

  // Warmup template management - API-based with localStorage fallback
  async getWarmupTemplates(): Promise<LocalWarmupTemplate[]> {
    try {
      // Get license context
      const licenseContext = getLicenseContext()
      if (!licenseContext) {
        console.warn('Invalid license context for warmup templates')
        return []
      }
      
      // Get license-specific storage key
      const licenseKey = licenseContext.licenseKey
      const storageKey = `fsn_warmup_templates_${licenseKey}`
      const oldStorageKey = 'warmupTemplates' // Old storage key
      
      console.log('🔥 WARMUP - Loading from localStorage...')
      
      // Try license-aware storage first
      let storedTemplates = this.getItem<LocalWarmupTemplate[]>(storageKey) || []
      
      // If no templates found in license-aware storage, check old storage key
      if (storedTemplates.length === 0) {
        console.log('🔥 WARMUP - No templates in license-aware storage, checking old storage key...')
        const oldTemplates = this.getItem<LocalWarmupTemplate[]>(oldStorageKey) || []
        if (oldTemplates.length > 0) {
          console.log(`🔥 WARMUP - Found ${oldTemplates.length} templates in old storage, migrating...`)
          // Migrate to license-aware storage
          this.setItem(storageKey, oldTemplates)
          // Remove from old storage
          localStorage.removeItem(oldStorageKey)
          storedTemplates = oldTemplates
        }
      }
      
      console.log(`✅ WARMUP - Loaded ${storedTemplates.length} warmup templates from localStorage`)
      console.log('🔥 WARMUP - Template details:', storedTemplates.map(t => ({
        id: t.id,
        name: t.name,
        platform: t.platform,
        createdAt: t.createdAt
      })))
      
      return storedTemplates
    } catch (error) {
      console.warn('Failed to fetch warmup templates:', error)
      return []
    }
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

  async addWarmupTemplate(template: LocalWarmupTemplate): Promise<void> {
    try {
      // Try API first
      const templateData: WarmupTemplateCreate = {
        name: template.name,
        description: template.name,
        platform: template.platform,
        phase: 'phase_1', // Default phase
        actions: [],
        settings: {
          captionsFile: template.captionsFile,
          photosPostsPerDay: template.photosPostsPerDay,
          photosFolder: template.photosFolder,
          textPostsPerDay: template.textPostsPerDay,
          textPostsFile: template.textPostsFile,
          followsPerDay: template.followsPerDay,
          likesPerDay: template.likesPerDay,
          scrollingTimeMinutes: template.scrollingTimeMinutes
        },
        is_active: true
      }
      
      const apiTemplate = await warmupAPI.createWarmupTemplate(templateData)
      
      // Update local template with API response
      const updatedTemplate: LocalTemplate = {
        ...template,
        id: apiTemplate.data.id.toString(),
        createdAt: apiTemplate.data.created_at,
        updatedAt: apiTemplate.data.updated_at
      }
      
      // Update localStorage
      const templates = this.getItem<LocalTemplate[]>('warmupTemplates') || []
      templates.push(updatedTemplate)
      this.setItem('warmupTemplates', templates)
      
    } catch (error) {
      console.warn('Failed to create warmup template via API, using localStorage fallback:', error)
      // Fallback to localStorage
      const templates = this.getItem<LocalTemplate[]>('warmupTemplates') || []
      templates.push(template)
      this.setItem('warmupTemplates', templates)
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
