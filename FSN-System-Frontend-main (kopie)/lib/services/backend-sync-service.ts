/**
 * Backend Sync Service
 * 
 * Handles synchronization between local storage and backend API
 * Ensures data consistency and provides fallback mechanisms
 */

import { localStorageService, LocalAccount, LocalDevice, LocalTemplate } from './local-storage-service'

// API endpoints (these would be configured based on environment)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class BackendSyncService {
  private isOnline: boolean = true

  constructor() {
    // Monitor online/offline status
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => {
        this.isOnline = true
        this.syncPendingChanges()
      })
      
      window.addEventListener('offline', () => {
        this.isOnline = false
      })
    }
  }

  // Generic API call method
  private async apiCall<T>(endpoint: string, method: string = 'GET', data?: any): Promise<T> {
    if (!this.isOnline) {
      throw new Error('No internet connection')
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    })

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`)
    }

    return response.json()
  }

  // Account synchronization
  async syncAccounts(): Promise<void> {
    try {
      const localAccounts = localStorageService.getAccounts()
      
      // Convert local accounts to backend format
      const backendAccounts = localAccounts.map(account => ({
        username: account.instagram_username || account.threads_username || '',
        email: account.email,
        phone: account.twoFactorCode, // Map 2FA code to phone field
        password: account.password,
        platform: account.platform,
        instagram_username: account.instagram_username,
        threads_username: account.threads_username,
        model_id: account.model ? parseInt(account.model) : null,
        device_id: account.device_id ? parseInt(account.device_id) : null,
        status: account.status,
        warmup_phase: account.warmup_phase,
        bio: account.notes,
        followers_count: account.followers_count || 0,
        following_count: 0,
        posts_count: 0,
        last_activity: account.updated_at,
        settings: {}
      }))

      // Sync each account
      for (const account of backendAccounts) {
        try {
          await this.apiCall('/accounts', 'POST', account)
          console.log(`Synced account: ${account.username}`)
        } catch (error) {
          console.error(`Failed to sync account ${account.username}:`, error)
        }
      }
    } catch (error) {
      console.error('Failed to sync accounts:', error)
    }
  }

  // Device synchronization
  async syncDevices(): Promise<void> {
    try {
      const localDevices = localStorageService.getDevices()
      
      // Convert local devices to backend format
      const backendDevices = localDevices.map(device => ({
        name: device.name,
        udid: device.udid,
        model: device.model,
        ios_version: device.ios_version,
        appium_port: device.appium_port,
        wda_port: device.wda_port,
        mjpeg_port: device.mjpeg_port,
        status: device.status,
        last_seen: device.last_seen
      }))

      // Sync each device
      for (const device of backendDevices) {
        try {
          await this.apiCall('/devices', 'POST', device)
          console.log(`Synced device: ${device.name}`)
        } catch (error) {
          console.error(`Failed to sync device ${device.name}:`, error)
        }
      }
    } catch (error) {
      console.error('Failed to sync devices:', error)
    }
  }

  // Template synchronization
  async syncTemplates(): Promise<void> {
    try {
      const localTemplates = localStorageService.getTemplates()
      
      // Convert local templates to backend format
      const backendTemplates = localTemplates.map(template => ({
        name: template.name,
        platform: template.platform,
        posts_per_day: template.photosPostsPerDay + template.textPostsPerDay,
        likes_per_day: template.likesPerDay,
        follows_per_day: template.followsPerDay,
        stories_per_day: 0,
        comments_per_day: 0,
        photos_per_day: template.photosPostsPerDay,
        text_posts_per_day: template.textPostsPerDay,
        captions_per_day: 0,
        reels_per_day: 0,
        photos_folder: template.photosFolder || '',
        text_posts_folder: template.textPostsFile || '',
        captions_folder: template.captionsFile || '',
        reels_folder: '',
        stories_folder: ''
      }))

      // Sync each template
      for (const template of backendTemplates) {
        try {
          await this.apiCall('/templates', 'POST', template)
          console.log(`Synced template: ${template.name}`)
        } catch (error) {
          console.error(`Failed to sync template ${template.name}:`, error)
        }
      }
    } catch (error) {
      console.error('Failed to sync templates:', error)
    }
  }

  // Sync all data
  async syncAllData(): Promise<void> {
    console.log('Starting full data synchronization...')
    
    try {
      await Promise.all([
        this.syncAccounts(),
        this.syncDevices(),
        this.syncTemplates()
      ])
      
      console.log('Data synchronization completed successfully')
    } catch (error) {
      console.error('Data synchronization failed:', error)
    }
  }

  // Sync pending changes (called when coming back online)
  private async syncPendingChanges(): Promise<void> {
    console.log('Syncing pending changes...')
    await this.syncAllData()
  }

  // Get data from backend and update local storage
  async pullDataFromBackend(): Promise<void> {
    try {
      // Pull accounts
      const accounts = await this.apiCall<LocalAccount[]>('/accounts')
      localStorageService.saveAccounts(accounts)

      // Pull devices
      const devices = await this.apiCall<LocalDevice[]>('/devices')
      localStorageService.saveDevices(devices)

      // Pull templates
      const templates = await this.apiCall<LocalTemplate[]>('/templates')
      localStorageService.saveTemplates(templates)

      console.log('Data pulled from backend successfully')
    } catch (error) {
      console.error('Failed to pull data from backend:', error)
    }
  }

  // Check if backend is available
  async checkBackendHealth(): Promise<boolean> {
    try {
      await this.apiCall('/health')
      return true
    } catch (error) {
      return false
    }
  }

  // Get sync status
  getSyncStatus(): { isOnline: boolean; lastSync?: Date } {
    return {
      isOnline: this.isOnline,
      lastSync: this.getLastSyncTime()
    }
  }

  private getLastSyncTime(): Date | undefined {
    const lastSync = localStorage.getItem('lastSyncTime')
    return lastSync ? new Date(lastSync) : undefined
  }

  private setLastSyncTime(): void {
    localStorage.setItem('lastSyncTime', new Date().toISOString())
  }

  // Manual sync trigger
  async triggerSync(): Promise<void> {
    if (this.isOnline) {
      await this.syncAllData()
      this.setLastSyncTime()
    } else {
      console.warn('Cannot sync: no internet connection')
    }
  }
}

// Export singleton instance
export const backendSyncService = new BackendSyncService()

// Auto-sync when the service is imported (if online)
if (typeof window !== 'undefined') {
  // Check if we should auto-sync (e.g., every 5 minutes)
  const lastSync = localStorage.getItem('lastSyncTime')
  const now = new Date()
  const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000)
  
  if (!lastSync || new Date(lastSync) < fiveMinutesAgo) {
    backendSyncService.triggerSync()
  }
}
