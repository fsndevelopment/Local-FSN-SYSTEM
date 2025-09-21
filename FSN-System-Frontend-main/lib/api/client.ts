/**
 * API Client Configuration for FSN Appium Farm
 * 
 * Centralized API client with proper error handling and type safety
 */

import { QueryClient } from '@tanstack/react-query'
import { getPlatform } from '@/lib/platform'

// Resolve base URL safely in both server and browser environments
function getBaseURL(): string {
  const envUrl = (globalThis as any)?.process?.env?.NEXT_PUBLIC_API_URL as string | undefined
  if (envUrl && envUrl.trim().length > 0) return envUrl
  const stored = getStoredBackendURL()
  if (stored && stored.trim().length > 0) return stored
  return 'http://localhost:8000'
}

// API Configuration - supports dynamic local storage override
export const API_CONFIG = {
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
}

// Get stored backend URL from localStorage (for ngrok URLs)
function getStoredBackendURL(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('fsn_backend_url')
}

// Set backend URL (for ngrok URLs)
export function setBackendURL(url: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('fsn_backend_url', url)
    // Reload page to apply new URL
    window.location.reload()
  }
}

// Create React Query client with optimized settings
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount: number, error: any) => {
        console.log('Query retry attempt:', { failureCount, error })
        // Don't retry on 4xx errors
        if (error?.status >= 400 && error?.status < 500) {
          return false
        }
        return failureCount < 3
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
})

// API Error types
export interface APIError {
  detail: string
  status?: number
  error_id?: string
}

// Generic API response wrapper
export interface APIResponse<T> {
  data: T
  status: number
  message?: string
}

/**
 * Generic API client function with proper error handling
 */
export async function apiClient<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_CONFIG.baseURL}${endpoint}`
  
  console.log('🔍 API Request:', { url, endpoint, baseURL: API_CONFIG.baseURL })
  
  const config: RequestInit = {
    ...options,
    headers: {
      ...API_CONFIG.headers,
      'X-Platform': getPlatform(),
      ...options.headers,
    },
  }

  try {
    console.log('📡 Making fetch request:', { url, config })
    const response = await fetch(url, config)
    console.log('📊 Response received:', { status: response.status, ok: response.ok })
    
    // Handle different response types
    const contentType = response.headers.get('content-type')
    let data: any
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    // Handle HTTP errors
    if (!response.ok) {
      const error: APIError = {
        detail: data?.detail || `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        error_id: data?.error_id,
      }
      throw error
    }

    return data
  } catch (error: any) {
    // Network or parsing errors
    if (!error.status) {
      throw {
        detail: 'Network error or server unavailable',
        status: 0,
      } as APIError
    }
    
    throw error
  }
}

/**
 * Convenience methods for different HTTP methods
 */
export const api = {
  get: <T = any>(endpoint: string, params?: Record<string, any>): Promise<T> => {
    const searchParams = params ? new URLSearchParams(params).toString() : ''
    const url = searchParams ? `${endpoint}?${searchParams}` : endpoint
    return apiClient<T>(url, { method: 'GET' })
  },

  post: <T = any>(endpoint: string, data?: any): Promise<T> => {
    return apiClient<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  },

  put: <T = any>(endpoint: string, data?: any): Promise<T> => {
    return apiClient<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  },

  delete: <T = any>(endpoint: string): Promise<T> => {
    return apiClient<T>(endpoint, { method: 'DELETE' })
  },

  patch: <T = any>(endpoint: string, data?: any): Promise<T> => {
    return apiClient<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  },
}

/**
 * Health check function to verify API connectivity
 */
export async function checkAPIHealth(): Promise<boolean> {
  try {
    await api.get('/health')
    return true
  } catch (error) {
    console.error('API health check failed:', error)
    return false
  }
}
