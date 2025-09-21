/**
 * Jobs API Client
 * 
 * TypeScript API client for job queue management operations
 */

import { api } from './client';

// Job Types
export interface Job {
  id: number;
  account_id: number;
  platform: 'instagram' | 'threads';
  type: JobType;
  status: JobStatus;
  priority: JobPriority;
  payload: Record<string, any>;
  not_before?: string;
  deadline?: string;
  attempts: number;
  max_attempts: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  result?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export type JobType = 
  // Instagram Jobs
  | 'instagram_follow_user'
  | 'instagram_unfollow_user'
  | 'instagram_like_post'
  | 'instagram_comment_post'
  | 'instagram_post_reel'
  | 'instagram_post_story'
  | 'instagram_view_story'
  | 'instagram_direct_message'
  | 'instagram_profile_update'
  | 'instagram_account_warmup'
  // Threads Jobs
  | 'threads_follow_user'
  | 'threads_unfollow_user'
  | 'threads_like_post'
  | 'threads_comment_post'
  | 'threads_create_post'
  | 'threads_repost'
  | 'threads_quote_post'
  | 'threads_direct_message'
  | 'threads_profile_update'
  | 'threads_account_warmup';

export type JobStatus = 
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'retrying';

export type JobPriority = 
  | 'low'
  | 'normal'
  | 'high'
  | 'urgent';

export interface JobCreate {
  account_id: number;
  platform: 'instagram' | 'threads';
  type: JobType;
  payload: Record<string, any>;
  priority?: JobPriority;
  not_before?: string;
  deadline?: string;
  max_attempts?: number;
}

export interface JobUpdate {
  status?: JobStatus;
  priority?: JobPriority;
  not_before?: string;
  deadline?: string;
  max_attempts?: number;
  payload?: Record<string, any>;
}

export interface JobsListResponse {
  items: Job[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface JobsFilters {
  status?: JobStatus;
  platform?: 'instagram' | 'threads';
  type?: JobType;
  priority?: JobPriority;
  account_id?: number;
  page?: number;
  size?: number;
}

export interface JobStats {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  retrying_jobs: number;
  instagram_jobs: number;
  threads_jobs: number;
  follow_jobs: number;
  like_jobs: number;
  comment_jobs: number;
  post_jobs: number;
  warmup_jobs: number;
  instagram_success_rate: number;
  threads_success_rate: number;
  success_rate: number;
  avg_execution_time?: number;
  jobs_per_hour: number;
}

// API Functions
export const getJobs = async (filters?: JobsFilters): Promise<JobsListResponse> => {
  const params = new URLSearchParams();
  
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });
  }
  
  const queryString = params.toString();
  const url = `/api/v1/jobs${queryString ? `?${queryString}` : ''}`;
  
  return await api.get(url);
};

export const getJob = async (id: number): Promise<Job> => {
  return await api.get(`/api/v1/jobs/${id}`);
};

export const createJob = async (data: JobCreate): Promise<Job> => {
  return await api.post('/api/v1/jobs', data);
};

export const updateJob = async (id: number, data: JobUpdate): Promise<Job> => {
  return await api.put(`/api/v1/jobs/${id}`, data);
};

export const deleteJob = async (id: number): Promise<void> => {
  await api.delete(`/api/v1/jobs/${id}`);
};

export const getJobStats = async (): Promise<JobStats> => {
  return await api.get('/api/v1/jobs/stats');
};

// Job Actions
export const cancelJob = async (id: number): Promise<Job> => {
  return await api.post(`/api/v1/jobs/${id}/cancel`);
};

export const retryJob = async (id: number): Promise<Job> => {
  return await api.post(`/api/v1/jobs/${id}/retry`);
};

export const pauseJob = async (id: number): Promise<Job> => {
  return await api.post(`/api/v1/jobs/${id}/pause`);
};

export const resumeJob = async (id: number): Promise<Job> => {
  return await api.post(`/api/v1/jobs/${id}/resume`);
};

// Bulk Operations
export const createBulkJobs = async (jobs: JobCreate[]): Promise<{
  created_count: number;
  failed_count: number;
  created_jobs: Job[];
  errors: Array<{ job: JobCreate; error: string }>;
}> => {
  return await api.post('/api/v1/jobs/bulk', { jobs });
};

export const cancelBulkJobs = async (job_ids: number[]): Promise<{
  cancelled_count: number;
  failed_count: number;
  results: Array<{ job_id: number; success: boolean; error?: string }>;
}> => {
  return await api.post('/api/v1/jobs/bulk/cancel', { job_ids });
};
