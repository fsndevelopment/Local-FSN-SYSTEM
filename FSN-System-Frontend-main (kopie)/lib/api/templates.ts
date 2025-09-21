/**
 * Templates API Service
 * 
 * Handles all template-related API calls with license-based isolation
 */

import { getLicenseContext } from '@/lib/services/license-api-service'
import { apiClient } from './client'

// Template interfaces
export interface Template {
  id: number
  name: string
  description?: string
  platform: 'instagram' | 'threads'
  actions: any[]
  settings: any
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TemplateCreate {
  name: string
  description?: string
  platform: 'instagram' | 'threads'
  actions: any[]
  settings: any
  is_active?: boolean
}

export interface TemplateUpdate {
  name?: string
  description?: string
  platform?: 'instagram' | 'threads'
  actions?: any[]
  settings?: any
  is_active?: boolean
}

// API Response interfaces
interface ApiResponse<T> {
  data: T
  message?: string
}

interface TemplateListResponse {
  items: Template[]
  total: number
  page: number
  size: number
  pages: number
}

class TemplatesAPI {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : 'http://localhost:8000/api'

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const licenseContext = getLicenseContext()
    console.log('🔍 TEMPLATES API - License context:', licenseContext)
    
    if (!licenseContext) {
      console.error('❌ TEMPLATES API - No license context found')
      throw new Error('License key required. Please provide X-License-Key header.')
    }
    
    const headers = {
      'X-License-Key': licenseContext.licenseKey,
      'X-Device-ID': licenseContext.deviceId,
      ...options.headers,
    }
    
    console.log('🔍 TEMPLATES API - Headers:', headers)

    try {
      const data = await apiClient<T>(endpoint, {
        ...options,
        headers,
      })
      return { data }
    } catch (error: any) {
      console.error('❌ TEMPLATES API - Request failed:', error)
      throw new Error(error.detail || `Failed to fetch templates: ${error.message}`)
    }
  }

  // Get all templates for the current license
  async getTemplates(filters?: {
    skip?: number
    limit?: number
    platform?: string
    is_active?: boolean
    search?: string
  }): Promise<ApiResponse<TemplateListResponse>> {
    const queryParams = new URLSearchParams()
    if (filters?.skip) queryParams.append('skip', filters.skip.toString())
    if (filters?.limit) queryParams.append('limit', filters.limit.toString())
    if (filters?.platform) queryParams.append('platform', filters.platform)
    if (filters?.is_active !== undefined) queryParams.append('is_active', filters.is_active.toString())
    if (filters?.search) queryParams.append('search', filters.search)
    
    const queryString = queryParams.toString()
    const endpoint = `/api/v1/templates${queryString ? `?${queryString}` : ''}`
    
    return this.makeRequest<TemplateListResponse>(endpoint)
  }

  // Get a specific template by ID
  async getTemplate(id: number): Promise<ApiResponse<Template>> {
    return this.makeRequest<Template>(`/api/v1/templates/${id}`)
  }

  // Create a new template
  async createTemplate(templateData: TemplateCreate): Promise<ApiResponse<Template>> {
    return this.makeRequest<Template>('/api/v1/templates', {
      method: 'POST',
      body: JSON.stringify(templateData),
    })
  }

  // Update an existing template
  async updateTemplate(id: number, templateData: TemplateUpdate): Promise<ApiResponse<Template>> {
    return this.makeRequest<Template>(`/api/v1/templates/${id}`, {
      method: 'PUT',
      body: JSON.stringify(templateData),
    })
  }

  // Delete a template
  async deleteTemplate(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest<{ message: string }>(`/api/v1/templates/${id}`, {
      method: 'DELETE',
    })
  }

  // Duplicate a template
  async duplicateTemplate(id: number, newName: string): Promise<ApiResponse<Template>> {
    return this.makeRequest<Template>(`/api/v1/templates/${id}/duplicate`, {
      method: 'POST',
      body: JSON.stringify({ name: newName }),
    })
  }

  // Execute a template (start job)
  async executeTemplate(id: number, accountIds: number[]): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/v1/templates/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ account_ids: accountIds }),
    })
  }

  // Stop a template execution
  async stopTemplate(id: number): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/v1/templates/${id}/stop`, {
      method: 'POST',
    })
  }
}

// Export singleton instance
export const templatesAPI = new TemplatesAPI()

// Export as templateAPI for backward compatibility
export const templateAPI = templatesAPI

// Export query keys for React Query
export const templateQueryKeys = {
  all: ['templates'] as const,
  lists: () => [...templateQueryKeys.all, 'list'] as const,
  list: (params?: any) => [...templateQueryKeys.lists(), params] as const,
  details: () => [...templateQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...templateQueryKeys.details(), id] as const,
}