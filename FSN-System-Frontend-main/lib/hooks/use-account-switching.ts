/**
 * React Query hooks for Account Switching
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { accountSwitchingApi, type AccountSwitchRequest, type AvailableAccountsResponse } from '@/lib/api/account-switching'

// Query keys
export const accountSwitchingKeys = {
  all: ['account-switching'] as const,
  availableAccounts: (deviceUdid: string, platform: string) => 
    [...accountSwitchingKeys.all, 'available-accounts', deviceUdid, platform] as const,
}

/**
 * Get available accounts on a device
 */
export function useAvailableAccounts(deviceUdid: string, platform: 'instagram' | 'threads', enabled: boolean = true) {
  return useQuery({
    queryKey: accountSwitchingKeys.availableAccounts(deviceUdid, platform),
    queryFn: () => accountSwitchingApi.getAvailableAccounts({ device_udid: deviceUdid, platform }),
    enabled: enabled && !!deviceUdid,
    staleTime: 30000, // 30 seconds
    retry: 2,
  })
}

/**
 * Launch app and navigate to profile tab
 */
export function useLaunchApp() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: Omit<AccountSwitchRequest, 'target_username'>) => 
      accountSwitchingApi.launchApp(request),
    onSuccess: (data, variables) => {
      // Invalidate available accounts query to refresh the list
      queryClient.invalidateQueries({
        queryKey: accountSwitchingKeys.availableAccounts(variables.device_udid, variables.platform)
      })
    },
  })
}

/**
 * Open account switcher dropdown
 */
export function useOpenSwitcher() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: Omit<AccountSwitchRequest, 'target_username'>) => 
      accountSwitchingApi.openSwitcher(request),
    onSuccess: (data, variables) => {
      // Invalidate available accounts query to refresh the list
      queryClient.invalidateQueries({
        queryKey: accountSwitchingKeys.availableAccounts(variables.device_udid, variables.platform)
      })
    },
  })
}

/**
 * Switch to a specific account
 */
export function useSwitchAccount() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: AccountSwitchRequest) => 
      accountSwitchingApi.switchAccount(request),
    onSuccess: (data, variables) => {
      // Invalidate available accounts query to refresh the list
      queryClient.invalidateQueries({
        queryKey: accountSwitchingKeys.availableAccounts(variables.device_udid, variables.platform)
      })
    },
  })
}

/**
 * Switch to account only (assumes switcher is already open)
 */
export function useSwitchToAccount() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: AccountSwitchRequest) => 
      accountSwitchingApi.switchToAccount(request),
    onSuccess: (data, variables) => {
      // Invalidate available accounts query to refresh the list
      queryClient.invalidateQueries({
        queryKey: accountSwitchingKeys.availableAccounts(variables.device_udid, variables.platform)
      })
    },
  })
}
