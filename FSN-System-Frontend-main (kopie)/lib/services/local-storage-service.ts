/**
 * Local Storage Service
 * 
 * Centralized service for managing all local storage operations
 * Ensures data persistence and consistency across the application
 */

import { Device, Template } from '@/lib/types'

// Storage keys
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

// Model interface for local storage
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

class LocalStorageService {
  // Generic storage methods
  private getItem<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error(`Failed to parse ${key} from localStorage:`, error)
      return null
    }
  }

  private setItem<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Failed to save ${key} to localStorage:`, error)
    }
  }

  // Account management
  getAccounts(): LocalAccount[] {
    return this.getItem<LocalAccount[]>(STORAGE_KEYS.ACCOUNTS) || []
  }

  saveAccounts(accounts: LocalAccount[]): void {
    this.setItem(STORAGE_KEYS.ACCOUNTS, accounts)
  }

  addAccount(account: LocalAccount): void {
    const accounts = this.getAccounts()
    accounts.push(account)
    this.saveAccounts(accounts)
  }

  updateAccount(accountId: string, updates: Partial<LocalAccount>): void {
    const accounts = this.getAccounts()
    const index = accounts.findIndex(acc => acc.id === accountId)
    if (index !== -1) {
      accounts[index] = { ...accounts[index], ...updates }
      this.saveAccounts(accounts)
    }
  }

  deleteAccount(accountId: string): void {
    const accounts = this.getAccounts()
    const filtered = accounts.filter(acc => acc.id !== accountId)
    this.saveAccounts(filtered)
  }

  // Device management
  getDevices(): LocalDevice[] {
    return this.getItem<LocalDevice[]>(STORAGE_KEYS.DEVICES) || []
  }

  saveDevices(devices: LocalDevice[]): void {
    this.setItem(STORAGE_KEYS.DEVICES, devices)
  }

  addDevice(device: LocalDevice): void {
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

  // Template management
  getTemplates(): LocalTemplate[] {
    return this.getItem<LocalTemplate[]>(STORAGE_KEYS.TEMPLATES) || []
  }

  saveTemplates(templates: LocalTemplate[]): void {
    this.setItem(STORAGE_KEYS.TEMPLATES, templates)
  }

  addTemplate(template: LocalTemplate): void {
    const templates = this.getTemplates()
    templates.push(template)
    this.saveTemplates(templates)
  }

  updateTemplate(templateId: string, updates: Partial<LocalTemplate>): void {
    const templates = this.getTemplates()
    const index = templates.findIndex(t => t.id === templateId)
    if (index !== -1) {
      templates[index] = { ...templates[index], ...updates }
      this.saveTemplates(templates)
    }
  }

  deleteTemplate(templateId: string): void {
    const templates = this.getTemplates()
    const filtered = templates.filter(t => t.id !== templateId)
    this.saveTemplates(filtered)
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

  // Model management
  getModels(): LocalModel[] {
    return this.getItem<LocalModel[]>(STORAGE_KEYS.MODELS) || []
  }

  saveModels(models: LocalModel[]): void {
    this.setItem(STORAGE_KEYS.MODELS, models)
  }

  addModel(model: LocalModel): void {
    const models = this.getModels()
    models.push(model)
    this.saveModels(models)
  }

  updateModel(modelId: string, updates: Partial<LocalModel>): void {
    const models = this.getModels()
    const index = models.findIndex(m => m.id === modelId)
    if (index !== -1) {
      models[index] = { ...models[index], ...updates }
      this.saveModels(models)
    }
  }

  deleteModel(modelId: string): void {
    const models = this.getModels()
    const filtered = models.filter(m => m.id !== modelId)
    this.saveModels(filtered)
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
    
    keys.forEach(key => {
      if (key.startsWith(`log_${deviceId}_`)) {
        const log = this.getItem<DayLog>(key)
        if (log) {
          logs.push(log)
        }
      }
    })
    
    return logs.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  }

  deleteLogForDate(deviceId: string, date: string): void {
    const logKey = `log_${deviceId}_${date}`
    localStorage.removeItem(logKey)
  }

  // Utility methods
  clearAllData(): void {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key)
    })
  }

  exportData(): Record<string, any> {
    return {
      accounts: this.getAccounts(),
      devices: this.getDevices(),
      templates: this.getTemplates(),
      deviceTemplates: this.getDeviceTemplates(),
      accountDevices: this.getAccountDevices(),
      models: this.getModels()
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
  validateAndMigrateData(): void {
    // Ensure all required data structures exist
    if (!this.getAccounts()) this.saveAccounts([])
    if (!this.getDevices()) this.saveDevices([])
    if (!this.getTemplates()) this.saveTemplates([])
    if (!this.getDeviceTemplates()) this.saveDeviceTemplates({})
    if (!this.getAccountDevices()) this.saveAccountDevices({})
    if (!this.getModels()) this.saveModels([])
  }
}

// Export singleton instance
export const localStorageService = new LocalStorageService()

// Initialize data validation on import
if (typeof window !== 'undefined') {
  localStorageService.validateAndMigrateData()
}
