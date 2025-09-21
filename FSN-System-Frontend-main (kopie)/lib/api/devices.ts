/**
 * Device API Service
 * 
 * API functions for device management with proper TypeScript types
 */

import { api } from './client'

// Device Types (matching backend Pydantic schemas)
export interface Device {
  id: number
  name: string
  udid: string
  ios_version?: string
  model?: string
  appium_port: number
  wda_port: number
  mjpeg_port: number
  wda_bundle_id?: string
  jailbroken: boolean
  status: 'active' | 'offline' | 'error'
  last_seen: string
  proxy_pool_id?: number
  settings?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface DeviceCreate {
  name: string
  udid: string
  ios_version?: string
  model?: string
  appium_port?: number
  wda_port?: number
  mjpeg_port?: number
  wda_bundle_id?: string
  jailbroken: boolean
  proxy_pool_id?: number
  settings?: Record<string, any>
}

export interface DeviceUpdate {
  name?: string
  ios_version?: string
  model?: string
  appium_port?: number
  wda_port?: number
  mjpeg_port?: number
  wda_bundle_id?: string
  jailbroken?: boolean
  status?: string
  proxy_pool_id?: number
  settings?: Record<string, any>
}

export interface ProxyPool {
  id: number
  name: string
  endpoint: string
  username?: string
  password?: string
  rotation_enabled: boolean
  rotation_interval: number
  status: 'active' | 'inactive'
  last_rotation?: string
  created_at: string
  updated_at?: string
}

// Device API Functions
export const deviceAPI = {
  // Get all devices with optional filtering
  getDevices: async (params?: {
    skip?: number
    limit?: number
    status?: string
  }): Promise<Device[]> => {
    return api.get('/api/v1/devices', params)
  },

  // Get specific device by ID
  getDevice: async (id: number): Promise<Device> => {
    return api.get(`/api/v1/devices/${id}`)
  },

  // Create new device
  createDevice: async (deviceData: DeviceCreate): Promise<Device> => {
    return api.post('/api/v1/devices', deviceData)
  },

  // Update existing device
  updateDevice: async (id: number, deviceData: DeviceUpdate): Promise<Device> => {
    return api.put(`/api/v1/devices/${id}`, deviceData)
  },

  // Delete device
  deleteDevice: async (id: number): Promise<{ message: string }> => {
    return api.delete(`/api/v1/devices/${id}`)
  },

  // Send heartbeat for device
  deviceHeartbeat: async (id: number): Promise<{ message: string }> => {
    return api.post(`/api/v1/devices/${id}/heartbeat`)
  },

  // Get proxy pools
  getProxyPools: async (): Promise<ProxyPool[]> => {
    return api.get('/api/v1/proxy-pools')
  },
}

// React Query Keys for caching
export const deviceQueryKeys = {
  all: ['devices'] as const,
  lists: () => [...deviceQueryKeys.all, 'list'] as const,
  list: (params?: Record<string, any>) => [...deviceQueryKeys.lists(), params] as const,
  details: () => [...deviceQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...deviceQueryKeys.details(), id] as const,
  proxyPools: () => ['proxy-pools'] as const,
}
