/**
 * Device Management Hooks
 * 
 * React Query hooks for device API operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { 
  deviceAPI, 
  deviceQueryKeys, 
  Device, 
  DeviceCreate, 
  DeviceUpdate 
} from '@/lib/api/devices'
import { deviceAPI as licenseDeviceAPI } from '@/lib/services/license-api-service'
import { usePlatform } from '@/lib/platform'

// Get all devices with optional filtering
export function useDevices(params?: {
  skip?: number
  limit?: number
  status?: string
}) {
  const [platform] = usePlatform()
  return useQuery({
    queryKey: deviceQueryKeys.list({ ...(params || {}), platform }),
    queryFn: () => licenseDeviceAPI.getDevices(params),
    staleTime: 30 * 1000, // 30 seconds for device list
  })
}

// Get specific device by ID
export function useDevice(id: number) {
  return useQuery({
    queryKey: deviceQueryKeys.detail(id),
    queryFn: () => licenseDeviceAPI.getDevice(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute for device details
  })
}

// Get proxy pools
export function useProxyPools() {
  return useQuery({
    queryKey: deviceQueryKeys.proxyPools(),
    queryFn: () => deviceAPI.getProxyPools(),
    staleTime: 5 * 60 * 1000, // 5 minutes for proxy pools
  })
}

// Create device mutation
export function useCreateDevice() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (deviceData: DeviceCreate) => licenseDeviceAPI.createDevice(deviceData),
    retry: false, // Disable retry to prevent duplicate calls
    onSuccess: (newDevice) => {
      // Invalidate and refetch device lists
      queryClient.invalidateQueries({ queryKey: deviceQueryKeys.lists() })
      
      // Add the new device to the cache
      queryClient.setQueryData(
        deviceQueryKeys.detail(newDevice.id),
        newDevice
      )
      
      toast.success(`Device "${newDevice.name}" created successfully`)
    },
    onError: (error: any) => {
      toast.error(`Failed to create device: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Update device mutation
export function useUpdateDevice() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: DeviceUpdate }) => 
      licenseDeviceAPI.updateDevice(id, data),
    onSuccess: (updatedDevice) => {
      // Update the device in cache
      queryClient.setQueryData(
        deviceQueryKeys.detail(updatedDevice.id),
        updatedDevice
      )
      
      // Invalidate device lists to reflect changes
      queryClient.invalidateQueries({ queryKey: deviceQueryKeys.lists() })
      
      toast.success(`Device "${updatedDevice.name}" updated successfully`)
    },
    onError: (error: any) => {
      toast.error(`Failed to update device: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Delete device mutation
export function useDeleteDevice() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => licenseDeviceAPI.deleteDevice(id),
    onSuccess: (_, deletedId) => {
      // Remove device from cache
      queryClient.removeQueries({ queryKey: deviceQueryKeys.detail(deletedId) })
      
      // Invalidate device lists
      queryClient.invalidateQueries({ queryKey: deviceQueryKeys.lists() })
      
      toast.success('Device deleted successfully')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete device: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Device heartbeat mutation
export function useDeviceHeartbeat() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => licenseDeviceAPI.deviceHeartbeat(id),
    onSuccess: (_, deviceId) => {
      // Invalidate device details to refresh status
      queryClient.invalidateQueries({ queryKey: deviceQueryKeys.detail(deviceId) })
      queryClient.invalidateQueries({ queryKey: deviceQueryKeys.lists() })
      
      toast.success('Device heartbeat sent successfully')
    },
    onError: (error: any) => {
      toast.error(`Heartbeat failed: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Utility hook for device statistics
export function useDeviceStats() {
  const { data: devicesResponse, isLoading } = useDevices()
  
  // Handle both array format and paginated response format
  const devices = Array.isArray(devicesResponse) 
    ? devicesResponse 
    : devicesResponse?.devices || []
  
  const stats = {
    total: devices?.length || 0,
    active: devices?.filter(d => d.status === 'active').length || 0,
    offline: devices?.filter(d => d.status === 'offline').length || 0,
    error: devices?.filter(d => d.status === 'error').length || 0,
  }
  
  return { stats, isLoading }
}
