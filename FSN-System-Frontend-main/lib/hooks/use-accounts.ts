/**
 * React Query hooks for Account Management
 * 
 * Custom hooks for managing account data with React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/hooks/use-toast';
import { useLicenseProtection } from '@/lib/hooks/use-license-protection';
import {
  getAccounts,
  getAccount,
  createAccount,
  updateAccount,
  deleteAccount,
  getAccountStats,
  triggerAccountWarmup,
  pauseAccount,
  resumeAccount,
  syncAccountMetrics,
  type Account,
  type AccountCreate,
  type AccountUpdate,
  type AccountsFilters,
} from '@/lib/api/accounts';
import { usePlatform } from '@/lib/platform';

// Query Keys
export const accountKeys = {
  all: ['accounts'] as const,
  lists: () => [...accountKeys.all, 'list'] as const,
  list: (filters?: AccountsFilters) => [...accountKeys.lists(), filters] as const,
  details: () => [...accountKeys.all, 'detail'] as const,
  detail: (id: number) => [...accountKeys.details(), id] as const,
  stats: () => [...accountKeys.all, 'stats'] as const,
};

// Hooks for Account Queries
export const useAccounts = (filters?: AccountsFilters) => {
  const [platform] = usePlatform();
  const key = { ...(filters || {}), platform };
  return useQuery({
    queryKey: accountKeys.list(key),
    queryFn: async () => {
      const res = await getAccounts(filters)
      // If API returns mixed platforms, filter client-side by current selection
      if (res?.items) {
        res.items = res.items.filter((a) => {
          if (!a.platform) return true
          if (platform === 'instagram') return a.platform === 'instagram' || a.platform === 'both'
          return a.platform === 'threads' || a.platform === 'both'
        })
      }
      return res
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useAccount = (id: number) => {
  return useQuery({
    queryKey: accountKeys.detail(id),
    queryFn: () => getAccount(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useAccountStats = () => {
  return useQuery({
    queryKey: accountKeys.stats(),
    queryFn: getAccountStats,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Hooks for Account Mutations
export const useCreateAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAccount,
    onSuccess: (data) => {
      // Invalidate and refetch accounts list
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: accountKeys.stats() });
      
      // Add the new account to the cache
      queryClient.setQueryData(accountKeys.detail(data.id), data);
      
      toast({
        title: "Account created",
        description: `Account ${data.username} has been created successfully.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create account",
        description: error.response?.data?.detail || "An error occurred while creating the account.",
        variant: "destructive",
      });
    },
  });
};

export const useUpdateAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AccountUpdate }) => 
      updateAccount(id, data),
    onSuccess: (data) => {
      // Update the specific account in the cache
      queryClient.setQueryData(accountKeys.detail(data.id), data);
      
      // Invalidate accounts list to reflect changes
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: accountKeys.stats() });
      
      toast({
        title: "Account updated",
        description: `Account ${data.username} has been updated successfully.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to update account",
        description: error.response?.data?.detail || "An error occurred while updating the account.",
        variant: "destructive",
      });
    },
  });
};

export const useDeleteAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteAccount,
    onSuccess: (_, accountId) => {
      // Remove the account from the cache
      queryClient.removeQueries({ queryKey: accountKeys.detail(accountId) });
      
      // Invalidate accounts list
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: accountKeys.stats() });
      
      toast({
        title: "Account deleted",
        description: "The account has been deleted successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete account",
        description: error.response?.data?.detail || "An error occurred while deleting the account.",
        variant: "destructive",
      });
    },
  });
};

// Hooks for Account Actions
export const useTriggerAccountWarmup = () => {
  const queryClient = useQueryClient();
  const { requireLicense, checkPlatformAccess } = useLicenseProtection();

  return useMutation({
    mutationFn: async (accountId: number) => {
      // Check license before triggering warmup
      const hasLicense = await requireLicense("trigger account warmup");
      if (!hasLicense) {
        throw new Error("License required to trigger account warmup");
      }

      // Get account to check platform
      const account = await getAccount(accountId);
      if (!checkPlatformAccess(account.platform)) {
        throw new Error(`License does not include ${account.platform} platform access`);
      }

      return triggerAccountWarmup(accountId);
    },
    onSuccess: (data, accountId) => {
      // Invalidate account details to reflect warmup status
      queryClient.invalidateQueries({ queryKey: accountKeys.detail(accountId) });
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      
      toast({
        title: "Warmup triggered",
        description: data.message || "Account warmup has been triggered successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to trigger warmup",
        description: error.message || error.response?.data?.detail || "An error occurred while triggering account warmup.",
        variant: "destructive",
      });
    },
  });
};

export const usePauseAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: pauseAccount,
    onSuccess: (data) => {
      // Update account in cache
      queryClient.setQueryData(accountKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      
      toast({
        title: "Account paused",
        description: `Account ${data.username} has been paused.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to pause account",
        description: error.response?.data?.detail || "An error occurred while pausing the account.",
        variant: "destructive",
      });
    },
  });
};

export const useResumeAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resumeAccount,
    onSuccess: (data) => {
      // Update account in cache
      queryClient.setQueryData(accountKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      
      toast({
        title: "Account resumed",
        description: `Account ${data.username} has been resumed.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to resume account",
        description: error.response?.data?.detail || "An error occurred while resuming the account.",
        variant: "destructive",
      });
    },
  });
};

export const useSyncAccountMetrics = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncAccountMetrics,
    onSuccess: (data) => {
      // Update account in cache
      queryClient.setQueryData(accountKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: accountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: accountKeys.stats() });
      
      toast({
        title: "Metrics synced",
        description: `Metrics for ${data.username} have been updated.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to sync metrics",
        description: error.response?.data?.detail || "An error occurred while syncing account metrics.",
        variant: "destructive",
      });
    },
  });
};
