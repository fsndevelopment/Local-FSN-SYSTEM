/**
 * React Query hooks for Job Queue Management
 * 
 * Custom hooks for managing job data with React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/hooks/use-toast';
import { useLicenseProtection } from '@/lib/hooks/use-license-protection';
import {
  getJobs,
  getJob,
  createJob,
  updateJob,
  deleteJob,
  getJobStats,
  cancelJob,
  retryJob,
  pauseJob,
  resumeJob,
  createBulkJobs,
  cancelBulkJobs,
  type Job,
  type JobCreate,
  type JobUpdate,
  type JobsFilters,
} from '@/lib/api/jobs';
import { usePlatform } from '@/lib/platform';

// Query Keys
export const jobKeys = {
  all: ['jobs'] as const,
  lists: () => [...jobKeys.all, 'list'] as const,
  list: (filters?: JobsFilters) => [...jobKeys.lists(), filters] as const,
  details: () => [...jobKeys.all, 'detail'] as const,
  detail: (id: number) => [...jobKeys.details(), id] as const,
  stats: () => [...jobKeys.all, 'stats'] as const,
};

// Hooks for Job Queries
export const useJobs = (filters?: JobsFilters) => {
  const [platform] = usePlatform();
  const key = { ...(filters || {}), platform };
  return useQuery({
    queryKey: jobKeys.list(key),
    queryFn: async () => {
      const res = await getJobs(filters)
      if (res?.items) {
        res.items = res.items.filter((j) => j.platform === platform)
      }
      return res
    },
    staleTime: 30 * 1000, // 30 seconds (jobs change frequently)
    refetchInterval: 60 * 1000, // Refetch every minute for real-time updates
  });
};

export const useJob = (id: number) => {
  return useQuery({
    queryKey: jobKeys.detail(id),
    queryFn: () => getJob(id),
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: (data) => {
      // Refetch more frequently for running jobs
      return data?.status === 'running' || data?.status === 'pending' ? 10 * 1000 : 60 * 1000;
    },
  });
};

export const useJobStats = () => {
  return useQuery({
    queryKey: jobKeys.stats(),
    queryFn: getJobStats,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
};

// Hooks for Job Mutations
export const useCreateJob = () => {
  const queryClient = useQueryClient();
  const { requireLicense, checkPlatformAccess } = useLicenseProtection();

  return useMutation({
    mutationFn: async (data: JobCreate) => {
      // Check license before creating job
      const hasLicense = await requireLicense("create job");
      if (!hasLicense) {
        throw new Error("License required to create jobs");
      }

      // Check platform access
      if (!checkPlatformAccess(data.platform)) {
        throw new Error(`License does not include ${data.platform} platform access`);
      }

      return createJob(data);
    },
    onSuccess: (data) => {
      // Invalidate and refetch jobs list
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      // Add the new job to the cache
      queryClient.setQueryData(jobKeys.detail(data.id), data);
      
      toast({
        title: "Job created",
        description: `${data.type} job has been created and queued.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create job",
        description: error.message || error.response?.data?.detail || "An error occurred while creating the job.",
        variant: "destructive",
      });
    },
  });
};

export const useUpdateJob = () => {
  const queryClient = useQueryClient();
  const { requireLicense } = useLicenseProtection();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: JobUpdate }) => {
      // Check license before updating job
      const hasLicense = await requireLicense("update job");
      if (!hasLicense) {
        throw new Error("License required to update jobs");
      }

      return updateJob(id, data);
    },
    onSuccess: (data) => {
      // Update the specific job in the cache
      queryClient.setQueryData(jobKeys.detail(data.id), data);
      
      // Invalidate jobs list to reflect changes
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast({
        title: "Job updated",
        description: `Job #${data.id} has been updated successfully.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to update job",
        description: error.message || error.response?.data?.detail || "An error occurred while updating the job.",
        variant: "destructive",
      });
    },
  });
};

export const useDeleteJob = () => {
  const queryClient = useQueryClient();
  const { requireLicense } = useLicenseProtection();

  return useMutation({
    mutationFn: async (jobId: number) => {
      // Check license before deleting job
      const hasLicense = await requireLicense("delete job");
      if (!hasLicense) {
        throw new Error("License required to delete jobs");
      }

      return deleteJob(jobId);
    },
    onSuccess: (_, jobId) => {
      // Remove the job from the cache
      queryClient.removeQueries({ queryKey: jobKeys.detail(jobId) });
      
      // Invalidate jobs list
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast({
        title: "Job deleted",
        description: "The job has been deleted successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete job",
        description: error.message || error.response?.data?.detail || "An error occurred while deleting the job.",
        variant: "destructive",
      });
    },
  });
};

// Hooks for Job Actions
export const useCancelJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelJob,
    onSuccess: (data) => {
      // Update job in cache
      queryClient.setQueryData(jobKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast({
        title: "Job cancelled",
        description: `Job #${data.id} has been cancelled.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to cancel job",
        description: error.response?.data?.detail || "An error occurred while cancelling the job.",
        variant: "destructive",
      });
    },
  });
};

export const useRetryJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: retryJob,
    onSuccess: (data) => {
      // Update job in cache
      queryClient.setQueryData(jobKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast({
        title: "Job retried",
        description: `Job #${data.id} has been queued for retry.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to retry job",
        description: error.response?.data?.detail || "An error occurred while retrying the job.",
        variant: "destructive",
      });
    },
  });
};

export const usePauseJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: pauseJob,
    onSuccess: (data) => {
      // Update job in cache
      queryClient.setQueryData(jobKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      
      toast({
        title: "Job paused",
        description: `Job #${data.id} has been paused.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to pause job",
        description: error.response?.data?.detail || "An error occurred while pausing the job.",
        variant: "destructive",
      });
    },
  });
};

export const useResumeJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resumeJob,
    onSuccess: (data) => {
      // Update job in cache
      queryClient.setQueryData(jobKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      
      toast({
        title: "Job resumed",
        description: `Job #${data.id} has been resumed.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to resume job",
        description: error.response?.data?.detail || "An error occurred while resuming the job.",
        variant: "destructive",
      });
    },
  });
};

// Bulk Operations
export const useCreateBulkJobs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBulkJobs,
    onSuccess: (data) => {
      // Invalidate jobs list and stats
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast({
        title: "Bulk jobs created",
        description: `${data.created_count} jobs created successfully. ${data.failed_count} failed.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create bulk jobs",
        description: error.response?.data?.detail || "An error occurred while creating bulk jobs.",
        variant: "destructive",
      });
    },
  });
};

export const useCancelBulkJobs = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelBulkJobs,
    onSuccess: (data) => {
      // Invalidate jobs list and stats
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast({
        title: "Bulk jobs cancelled",
        description: `${data.cancelled_count} jobs cancelled successfully.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to cancel bulk jobs",
        description: error.response?.data?.detail || "An error occurred while cancelling bulk jobs.",
        variant: "destructive",
      });
    },
  });
};
