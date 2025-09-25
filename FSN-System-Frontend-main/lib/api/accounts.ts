/**
 * Accounts API Service
 * 
 * Handles all account-related API calls with license-based isolation
 */

import { getLicenseContext } from '@/lib/services/license-api-service'
import { apiClient } from './client'

// Account interfaces
export interface Account {
  id: number
  username: string
  platform: 'instagram' | 'threads'
  auth_type: '2fa' | 'non-2fa'
  email?: string
  two_factor_code?: string
  password: string
  model_id?: number
  device_id?: number
  notes?: string
  container_number?: number
  status: 'active' | 'inactive' | 'warming_up' | 'suspended' | 'banned'
  warmup_phase?: 'phase_1' | 'phase_2' | 'phase_3' | 'complete'
  last_activity?: string
  created_at: string
  updated_at: string
}

export interface AccountCreate {
  username: string
  platform: 'instagram' | 'threads'
  auth_type: '2fa' | 'non-2fa'
  email?: string
  two_factor_code?: string
  password: string
  model_id?: number
  device_id?: number
  notes?: string
  container_number?: number
}

export interface AccountUpdate {
  username?: string
  platform?: 'instagram' | 'threads'
  auth_type?: '2fa' | 'non-2fa'
  email?: string
  two_factor_code?: string
  password?: string
  model_id?: number
  device_id?: number
  notes?: string
  container_number?: number
  status?: 'active' | 'inactive' | 'warming_up' | 'suspended' | 'banned'
  warmup_phase?: 'phase_1' | 'phase_2' | 'phase_3' | 'complete'
  account_phase?: 'warmup' | 'posting' // Add account phase field
}

// API Response interfaces
interface ApiResponse<T> {
  data: T
  message?: string
}

interface AccountListResponse {
  items: Account[]
  total: number
  page: number
  size: number
  pages: number
}

class AccountsAPI {
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
      throw new Error(error.detail || `Failed to fetch accounts: ${error.message}`)
    }
  }

  // Get all accounts for the current license
  async getAccounts(filters?: {
    skip?: number
    limit?: number
    status?: string
    warmup_phase?: string
    device_id?: number
    search?: string
  }): Promise<ApiResponse<AccountListResponse>> {
    const queryParams = new URLSearchParams()
    if (filters?.skip) queryParams.append('skip', filters.skip.toString())
    if (filters?.limit) queryParams.append('limit', filters.limit.toString())
    if (filters?.status) queryParams.append('status', filters.status)
    if (filters?.warmup_phase) queryParams.append('warmup_phase', filters.warmup_phase)
    if (filters?.device_id) queryParams.append('device_id', filters.device_id.toString())
    if (filters?.search) queryParams.append('search', filters.search)
    
    const queryString = queryParams.toString()
    const endpoint = `/api/v1/accounts${queryString ? `?${queryString}` : ''}`
    
    return this.makeRequest<AccountListResponse>(endpoint)
  }

  // Get a specific account by ID
  async getAccount(id: number): Promise<ApiResponse<Account>> {
    return this.makeRequest<Account>(`/api/v1/accounts/${id}`)
  }

  // Create a new account
  async createAccount(accountData: AccountCreate): Promise<ApiResponse<Account>> {
    return this.makeRequest<Account>('/api/v1/accounts', {
      method: 'POST',
      body: JSON.stringify(accountData),
    })
  }

  // Update an existing account
  async updateAccount(id: number, accountData: AccountUpdate): Promise<ApiResponse<Account>> {
    return this.makeRequest<Account>(`/api/v1/accounts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(accountData),
    })
  }

  // Delete an account
  async deleteAccount(id: number): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest<{ message: string }>(`/api/v1/accounts/${id}`, {
      method: 'DELETE',
    })
  }

  // Get account statistics
  async getAccountStats(): Promise<ApiResponse<any>> {
    return this.makeRequest<any>('/api/v1/accounts/stats')
  }
}

// Export singleton instance
export const accountsAPI = new AccountsAPI()

// Export individual functions for convenience
export const getAccounts = (filters?: any) => accountsAPI.getAccounts(filters)
export const getAccount = (id: number) => accountsAPI.getAccount(id)
export const createAccount = (accountData: AccountCreate) => accountsAPI.createAccount(accountData)
export const updateAccount = (id: number, accountData: AccountUpdate) => accountsAPI.updateAccount(id, accountData)
export const deleteAccount = (id: number) => accountsAPI.deleteAccount(id)
export const getAccountStats = () => accountsAPI.getAccountStats()

// Additional functions that might be needed
export const triggerAccountWarmup = async (id: number) => {
  // This would need to be implemented in the backend
  throw new Error('triggerAccountWarmup not implemented')
}

export const pauseAccount = async (id: number) => {
  // This would need to be implemented in the backend
  throw new Error('pauseAccount not implemented')
}

export const resumeAccount = async (id: number) => {
  // This would need to be implemented in the backend
  throw new Error('resumeAccount not implemented')
}

export const syncAccountMetrics = async (id: number) => {
  // This would need to be implemented in the backend
  throw new Error('syncAccountMetrics not implemented')
}

// Export types
export type { Account, AccountCreate, AccountUpdate }
export type AccountsFilters = {
  skip?: number
  limit?: number
  status?: string
  warmup_phase?: string
  device_id?: number
  search?: string
}