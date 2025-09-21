/**
 * Warmup Templates API Service
 * 
 * Handles all warmup template-related API calls with license-based isolation
 */

import { getLicenseContext } from '@/lib/services/license-api-service'
import { apiClient } from './client'

// Warmup Template interfaces
export interface WarmupTemplate {
  id: number
  name: string
  description?: string
  platform: 'instagram' | 'threads'
  phase: 'phase_1' | 'phase_2' | 'phase_3'
  actions: any[]
  settings: any
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WarmupTemplateCreate {
  name: string
  description?: string
  platform: 'instagram' | 'threads'
  phase: 'phase_1' | 'phase_2' | 'phase_3'
  actions: any[]
  settings: any
  is_active?: boolean
}

export interface WarmupTemplateUpdate {
  name?: string
  description?: string
  platform?: 'instagram' | 'threads'
  phase?: 'phase_1' | 'phase_2' | 'phase_3'
  actions?: any[]
  settings?: any
  is_active?: boolean
}

// API Response interfaces
interface ApiResponse<T> {
  data: T
  message?: string
}

interface WarmupTemplateListResponse {
  items: WarmupTemplate[]
  total: number
  page: number
  size: number
  pages: number
}

class WarmupAPI {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : 'http://localhost:8000/api'

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      throw new Error('License key required. Please provide X-License-Key header.')
    }
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'X-License-Key': licenseContext.licenseKey,
      'X-Device-ID': licenseContext.deviceId,
    }

    try {
      const data = await apiClient<T>(endpoint, {
        ...options,
        headers: {
          'X-License-Key': licenseContext.licenseKey,
          'X-Device-ID': licenseContext.deviceId,
          ...options.headers,
        },
      })
      return { data }
    } catch (error: any) {
      throw new Error(error.detail || `Failed to fetch warmup templates: ${error.message}`)
    }
  }

  // Get all warmup templates for the current license
  async getWarmupTemplates(filters?: {
    skip?: number
    limit?: number
    platform?: string
    phase?: string
    is_active?: boolean
    search?: string
  }): Promise<ApiResponse<WarmupTemplateListResponse>> {
    const queryParams = new URLSearchParams()
    if (filters?.skip) queryParams.append('skip', filters.skip.toString())
    if (filters?.limit) queryParams.append('limit', filters.limit.toString())
    if (filters?.platform) queryParams.append('platform', filters.platform)
    if (filters?.phase) queryParams.append('phase', filters.phase)
    if (filters?.is_active !== undefined) queryParams.append('is_active', filters.is_active.toString())
    if (filters?.search) queryParams.append('search', filters.search)
    
    const queryString = queryParams.toString()
    const endpoint = `/api/v1/warmup-templates${queryString ? `?${queryString}` : ''}`
    
    return this.makeRequest<WarmupTemplateListResponse>(endpoint)
  }

  // Get a specific warmup template by ID
  async getWarmupTemplate(id: number): Promise<ApiResponse<WarmupTemplate>> {
    return this.makeRequest<WarmupTemplate>(`/api/v1/warmup-templates/${id}`)
  }

  // Create a new warmup template
  async createWarmupTemplate(templateData: WarmupTemplateCreate): Promise<ApiResponse<WarmupTemplate>> {
    return this.makeRequest<WarmupTemplate>('/api/v1/warmup-templates', {
      method: 'POST',
      body: JSON.stringify(templateData),
    })
  }

  // Update an existing warmup template
  async updateWarmupTemplate(id: number, templateData: WarmupTemplateUpdate): Promise<ApiResponse<WarmupTemplate>> {
    return this.makeRequest<WarmupTemplate>(`/api/v1/warmup-templates/${id}`, {
      method: 'PUT',
      body: JSON.stringify(templateData),
    })
  }

  // Delete a warmup template
  async deleteWarmupTemplate(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest<{ message: string }>(`/api/v1/warmup-templates/${id}`, {
      method: 'DELETE',
    })
  }

  // Duplicate a warmup template
  async duplicateWarmupTemplate(id: number, newName: string): Promise<ApiResponse<WarmupTemplate>> {
    return this.makeRequest<WarmupTemplate>(`/api/v1/warmup-templates/${id}/duplicate`, {
      method: 'POST',
      body: JSON.stringify({ name: newName }),
    })
  }

  // Execute a warmup template (start warmup job)
  async executeWarmupTemplate(id: number, accountIds: number[]): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/v1/warmup-templates/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ account_ids: accountIds }),
    })
  }
}

// Export singleton instance
export const warmupAPI = new WarmupAPI()
