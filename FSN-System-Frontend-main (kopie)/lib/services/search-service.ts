/**
 * Search Service - Hybrid Frontend/Backend Search
 * 
 * Current: Filters existing API data client-side
 * Future: Will call dedicated search API endpoint
 */

import { localStorageService, type LocalDevice, type LocalAccount, type LocalModel, type LocalTemplate } from "./local-storage-service"

export interface SearchResult {
  id: string
  type: 'device' | 'account' | 'model' | 'template'
  title: string
  subtitle: string
  description: string
  status?: string
  platform?: string
  icon: string
  url: string
  metadata: Record<string, any>
}

export interface SearchFilters {
  type?: string
  status?: string
  platform?: string
  limit?: number
}

class SearchService {
  private searchData: {
    devices: LocalDevice[]
    accounts: LocalAccount[]
    models: LocalModel[]
    templates: LocalTemplate[]
  } = {
    devices: [],
    accounts: [],
    models: [],
    templates: []
  }

  /**
   * Initialize search data from local storage
   */
  loadData() {
    this.searchData.devices = localStorageService.getDevices()
    this.searchData.accounts = localStorageService.getAccounts()
    this.searchData.models = localStorageService.getModels()
    this.searchData.templates = localStorageService.getTemplates()
  }

  /**
   * Search across all data types
   */
  search(query: string, filters: SearchFilters = {}): SearchResult[] {
    if (!query.trim()) return []

    // Load fresh data from local storage
    this.loadData()

    const results: SearchResult[] = []
    const searchTerm = query.toLowerCase()

    // Search devices
    if (!filters.type || filters.type === 'device') {
      const deviceResults = this.searchDevices(searchTerm, filters)
      results.push(...deviceResults)
    }

    // Search accounts
    if (!filters.type || filters.type === 'account') {
      const accountResults = this.searchAccounts(searchTerm, filters)
      results.push(...accountResults)
    }

    // Search models
    if (!filters.type || filters.type === 'model') {
      const modelResults = this.searchModels(searchTerm, filters)
      results.push(...modelResults)
    }

    // Search templates
    if (!filters.type || filters.type === 'template') {
      const templateResults = this.searchTemplates(searchTerm, filters)
      results.push(...templateResults)
    }

    // Sort by relevance (exact matches first, then partial matches)
    return this.sortByRelevance(results, searchTerm).slice(0, filters.limit || 20)
  }

  /**
   * Search devices
   */
  private searchDevices(query: string, filters: SearchFilters): SearchResult[] {
    return this.searchData.devices
      .filter(device => {
        // Apply status filter
        if (filters.status && device.status !== filters.status) return false

        // Search in device fields
        const searchableText = [
          device.name,
          device.udid,
          device.ios_version,
          device.model,
          device.appium_port?.toString(),
          device.wda_port?.toString(),
          device.status
        ].join(' ').toLowerCase()

        return searchableText.includes(query)
      })
      .map(device => ({
        id: device.id.toString(),
        type: 'device' as const,
        title: device.name,
        subtitle: `Device • iOS ${device.ios_version} • ${device.status}`,
        description: `UDID: ${device.udid.substring(0, 8)}...${device.udid.substring(-6)}`,
        status: device.status,
        icon: '📱',
        url: `/devices/${device.id}`,
        metadata: {
          udid: device.udid,
          ios_version: device.ios_version,
          model: device.model,
          appium_port: device.appium_port,
          wda_port: device.wda_port
        }
      }))
  }

  /**
   * Search accounts
   */
  private searchAccounts(query: string, filters: SearchFilters): SearchResult[] {
    return this.searchData.accounts
      .filter(account => {
        // Apply platform filter
        if (filters.platform && account.platform !== filters.platform) return false

        // Apply status filter
        if (filters.status && account.status !== filters.status) return false

        // Search in account fields
        const searchableText = [
          account.instagram_username || '',
          account.threads_username || '',
          account.platform,
          account.status,
          account.warmup_phase,
          account.model || '',
          account.device || '',
          account.followers_count?.toString() || ''
        ].join(' ').toLowerCase()

        return searchableText.includes(query)
      })
      .map(account => ({
        id: account.id,
        type: 'account' as const,
        title: account.instagram_username || account.threads_username || 'Unknown',
        subtitle: `Account • ${account.platform} • ${account.status}`,
        description: `${account.followers_count?.toLocaleString() || 'NA'} followers • Model: ${account.model || 'N/A'}`,
        status: account.status,
        platform: account.platform,
        icon: '👤',
        url: `/accounts/${account.id}`,
        metadata: {
          platform: account.platform,
          warmup_phase: account.warmup_phase,
          followers_count: account.followers_count,
          model: account.model,
          device: account.device
        }
      }))
  }

  /**
   * Search models
   */
  private searchModels(query: string, filters: SearchFilters): SearchResult[] {
    return this.searchData.models
      .filter(model => {
        // Search in model fields
        const searchableText = [
          model.name,
          model.id
        ].join(' ').toLowerCase()

        return searchableText.includes(query)
      })
      .map(model => ({
        id: model.id,
        type: 'model' as const,
        title: model.name,
        subtitle: `Model • OnlyFans`,
        description: `Created: ${model.createdAt ? new Date(model.createdAt).toLocaleDateString() : 'Unknown'}`,
        icon: model.profilePhoto || '👩',
        url: `/models`,
        metadata: {
          name: model.name,
          profilePhoto: model.profilePhoto,
          createdAt: model.createdAt
        }
      }))
  }

  /**
   * Search templates
   */
  private searchTemplates(query: string, filters: SearchFilters): SearchResult[] {
    return this.searchData.templates
      .filter(template => {
        // Apply platform filter
        if (filters.platform && template.platform !== filters.platform) return false

        // Search in template fields
        const searchableText = [
          template.name,
          template.platform,
          template.postsPerDay?.toString() || '',
          template.likesPerDay?.toString() || '',
          template.followsPerDay?.toString() || '',
          template.storiesPerDay?.toString() || '',
          template.commentsPerDay?.toString() || ''
        ].join(' ').toLowerCase()

        return searchableText.includes(query)
      })
      .map(template => ({
        id: template.id,
        type: 'template' as const,
        title: template.name,
        subtitle: `Template • ${template.platform}`,
        description: `${template.postsPerDay} posts • ${template.likesPerDay} likes • ${template.followsPerDay} follows`,
        platform: template.platform,
        icon: '📋',
        url: `/templates`,
        metadata: {
          platform: template.platform,
          postsPerDay: template.postsPerDay,
          likesPerDay: template.likesPerDay,
          followsPerDay: template.followsPerDay
        }
      }))
  }


  /**
   * Sort results by relevance
   */
  private sortByRelevance(results: SearchResult[], query: string): SearchResult[] {
    return results.sort((a, b) => {
      const aTitle = a.title.toLowerCase()
      const bTitle = b.title.toLowerCase()
      const aSubtitle = a.subtitle.toLowerCase()
      const bSubtitle = b.subtitle.toLowerCase()

      // Exact title matches first
      if (aTitle === query && bTitle !== query) return -1
      if (bTitle === query && aTitle !== query) return 1

      // Title starts with query
      if (aTitle.startsWith(query) && !bTitle.startsWith(query)) return -1
      if (bTitle.startsWith(query) && !aTitle.startsWith(query)) return 1

      // Subtitle contains query
      if (aSubtitle.includes(query) && !bSubtitle.includes(query)) return -1
      if (bSubtitle.includes(query) && !aSubtitle.includes(query)) return 1

      // Alphabetical order
      return aTitle.localeCompare(bTitle)
    })
  }

  /**
   * Get search suggestions
   */
  getSuggestions(query: string, limit: number = 5): string[] {
    if (!query.trim()) return []

    // Load fresh data
    this.loadData()

    const suggestions: string[] = []
    const searchTerm = query.toLowerCase()

    // Add device names
    this.searchData.devices.forEach(device => {
      if (device.name.toLowerCase().includes(searchTerm)) {
        suggestions.push(device.name)
      }
    })

    // Add account usernames
    this.searchData.accounts.forEach(account => {
      const username = account.instagram_username || account.threads_username
      if (username && username.toLowerCase().includes(searchTerm)) {
        suggestions.push(username)
      }
    })

    // Add model names
    this.searchData.models.forEach(model => {
      if (model.name.toLowerCase().includes(searchTerm)) {
        suggestions.push(model.name)
      }
    })

    // Add template names
    this.searchData.templates.forEach(template => {
      if (template.name.toLowerCase().includes(searchTerm)) {
        suggestions.push(template.name)
      }
    })

    // Remove duplicates and limit
    return [...new Set(suggestions)].slice(0, limit)
  }
}

// Export singleton instance
export const searchService = new SearchService()

