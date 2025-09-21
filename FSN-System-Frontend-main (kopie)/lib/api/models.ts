/**
 * Models API Service
 * 
 * Handles all model-related API calls with license-based isolation
 */

import { getLicenseContext } from '@/lib/services/license-api-service'
import { apiClient } from './client'

// Model interface
export interface Model {
  id: string
  name: string
  profilePhoto?: string
  created_at: string
  updated_at: string
}

// API Response interfaces
interface ApiResponse<T> {
  data: T
  message?: string
}

interface ModelListResponse {
  items: Model[]
  total: number
  skip: number
  limit: number
}

class ModelsAPI {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : 'http://localhost:8000/api'

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const licenseContext = getLicenseContext()
    if (!licenseContext) {
      throw new Error('License key required. Please provide X-License-Key header.')
    }
    
    const headers = {
      'X-License-Key': licenseContext.licenseKey,
      'X-Device-ID': licenseContext.deviceId,
      ...options.headers,
    }

    try {
      const data = await apiClient<T>(endpoint, {
        ...options,
        headers,
      })
      return { data }
    } catch (error: any) {
      throw new Error(error.detail || `Failed to fetch models: ${error.message}`)
    }
  }

  // Get all models for the current license
  async getModels(filters?: any): Promise<ApiResponse<ModelListResponse>> {
    const queryParams = new URLSearchParams()
    if (filters?.skip) queryParams.append('skip', filters.skip.toString())
    if (filters?.limit) queryParams.append('limit', filters.limit.toString())
    
    const queryString = queryParams.toString()
    const endpoint = `/api/v1/models${queryString ? `?${queryString}` : ''}`
    
    return this.makeRequest<ModelListResponse>(endpoint)
  }

  // Get a specific model by ID
  async getModel(id: string): Promise<ApiResponse<Model>> {
    return this.makeRequest<Model>(`/api/v1/models/${id}`)
  }

  // Create a new model
  async createModel(modelData: Omit<Model, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Model>> {
    return this.makeRequest<Model>('/api/v1/models', {
      method: 'POST',
      body: JSON.stringify(modelData),
    })
  }

  // Update an existing model
  async updateModel(id: string, modelData: Partial<Model>): Promise<ApiResponse<Model>> {
    return this.makeRequest<Model>(`/api/v1/models/${id}`, {
      method: 'PUT',
      body: JSON.stringify(modelData),
    })
  }

  // Delete a model
  async deleteModel(id: string): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest<{ message: string }>(`/api/v1/models/${id}`, {
      method: 'DELETE',
    })
  }
}

// Export singleton instance
export const modelsAPI = new ModelsAPI()
