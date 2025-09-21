/**
 * Account Switching API Client
 * Handles switching between accounts on Instagram and Threads
 */

import { apiClient } from './client'

export interface AccountSwitchRequest {
  device_udid: string
  target_username: string
  platform: 'instagram' | 'threads'
}

export interface AccountSwitchResponse {
  success: boolean
  message: string
  data: {
    checkpoints?: any[]
    [key: string]: any
  }
}

export interface AvailableAccount {
  username: string
  full_name: string
  element?: any
}

export interface AvailableAccountsResponse {
  success: boolean
  message: string
  data: {
    accounts: AvailableAccount[]
  }
}

export const accountSwitchingApi = {
  /**
   * Complete account switching flow
   */
  async switchAccount(request: AccountSwitchRequest): Promise<AccountSwitchResponse> {
    const response = await apiClient.post('/api/v1/account-switching/switch', request)
    return response.data
  },

  /**
   * Launch app and navigate to profile tab
   */
  async launchApp(request: Omit<AccountSwitchRequest, 'target_username'>): Promise<AccountSwitchResponse> {
    const response = await apiClient.post('/api/v1/account-switching/launch', request)
    return response.data
  },

  /**
   * Open account switcher dropdown
   */
  async openSwitcher(request: Omit<AccountSwitchRequest, 'target_username'>): Promise<AccountSwitchResponse> {
    const response = await apiClient.post('/api/v1/account-switching/open-switcher', request)
    return response.data
  },

  /**
   * Get available accounts on device
   */
  async getAvailableAccounts(request: Omit<AccountSwitchRequest, 'target_username'>): Promise<AvailableAccountsResponse> {
    const response = await apiClient.post('/api/v1/account-switching/available-accounts', request)
    return response.data
  },

  /**
   * Switch to account (assumes switcher is already open)
   */
  async switchToAccount(request: AccountSwitchRequest): Promise<AccountSwitchResponse> {
    const response = await apiClient.post('/api/v1/account-switching/switch-only', request)
    return response.data
  }
}
