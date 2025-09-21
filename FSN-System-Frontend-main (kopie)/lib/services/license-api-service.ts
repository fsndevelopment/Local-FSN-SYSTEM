/**
 * License-Based API Service
 * 
 * Centralized service for all API operations that require license validation
 * Replaces local storage with server-based storage tied to license
 */

import { api } from '@/lib/api/client'

// License context for API calls
let currentLicense: { licenseKey: string; deviceId: string } | null = null

export function setLicenseContext(licenseKey: string, deviceId: string) {
  console.log('🔐 LICENSE API SERVICE - setLicenseContext called with:', { licenseKey, deviceId })
  currentLicense = { licenseKey, deviceId }
  console.log('🔐 LICENSE API SERVICE - currentLicense set to:', currentLicense)
}

export function getLicenseContext() {
  console.log('🔍 LICENSE API SERVICE - getLicenseContext called, context:', currentLicense)
  return currentLicense
}

// Helper function to add license headers to API calls
function getLicenseHeaders() {
  if (!currentLicense) {
    throw new Error('License context not set. Please validate license first.')
  }
  
  return {
    'X-License-Key': currentLicense.licenseKey,
    'X-Device-ID': currentLicense.deviceId,
  }
}

// Account management
export const accountAPI = {
  async getAccounts(params?: { skip?: number; limit?: number; status?: string }) {
    return api.get('/api/v1/accounts', params, { headers: getLicenseHeaders() })
  },

  async getAccount(id: string) {
    return api.get(`/api/v1/accounts/${id}`, undefined, { headers: getLicenseHeaders() })
  },

  async createAccount(accountData: any) {
    return api.post('/api/v1/accounts', accountData, { headers: getLicenseHeaders() })
  },

  async updateAccount(id: string, accountData: any) {
    return api.put(`/api/v1/accounts/${id}`, accountData, { headers: getLicenseHeaders() })
  },

  async deleteAccount(id: string) {
    return api.delete(`/api/v1/accounts/${id}`, { headers: getLicenseHeaders() })
  }
}

// Device management (already implemented but adding license headers)
export const deviceAPI = {
  async getDevices(params?: { skip?: number; limit?: number; status?: string }) {
    return api.get('/api/v1/devices', params, { headers: getLicenseHeaders() })
  },

  async getDevice(id: number) {
    return api.get(`/api/v1/devices/${id}`, undefined, { headers: getLicenseHeaders() })
  },

  async createDevice(deviceData: any) {
    return api.post('/api/v1/devices', deviceData, { headers: getLicenseHeaders() })
  },

  async updateDevice(id: number, deviceData: any) {
    return api.put(`/api/v1/devices/${id}`, deviceData, { headers: getLicenseHeaders() })
  },

  async deleteDevice(id: number) {
    return api.delete(`/api/v1/devices/${id}`, { headers: getLicenseHeaders() })
  },

  async deviceHeartbeat(id: number) {
    return api.post(`/api/v1/devices/${id}/heartbeat`, undefined, { headers: getLicenseHeaders() })
  }
}

// Template management
export const templateAPI = {
  async getTemplates(params?: { skip?: number; limit?: number; platform?: string }) {
    return api.get('/api/v1/templates', params, { headers: getLicenseHeaders() })
  },

  async getTemplate(id: string) {
    return api.get(`/api/v1/templates/${id}`, undefined, { headers: getLicenseHeaders() })
  },

  async createTemplate(templateData: any) {
    return api.post('/api/v1/templates', templateData, { headers: getLicenseHeaders() })
  },

  async updateTemplate(id: string, templateData: any) {
    return api.put(`/api/v1/templates/${id}`, templateData, { headers: getLicenseHeaders() })
  },

  async deleteTemplate(id: string) {
    return api.delete(`/api/v1/templates/${id}`, { headers: getLicenseHeaders() })
  }
}

// Model management
export const modelAPI = {
  async getModels(params?: { skip?: number; limit?: number }) {
    return api.get('/api/v1/models', params, { headers: getLicenseHeaders() })
  },

  async getModel(id: string) {
    return api.get(`/api/v1/models/${id}`, undefined, { headers: getLicenseHeaders() })
  },

  async createModel(modelData: any) {
    return api.post('/api/v1/models', modelData, { headers: getLicenseHeaders() })
  },

  async updateModel(id: string, modelData: any) {
    return api.put(`/api/v1/models/${id}`, modelData, { headers: getLicenseHeaders() })
  },

  async deleteModel(id: string) {
    return api.delete(`/api/v1/models/${id}`, { headers: getLicenseHeaders() })
  }
}

// Device template assignments
export const deviceTemplateAPI = {
  async getDeviceTemplates() {
    return api.get('/api/v1/device-templates', undefined, { headers: getLicenseHeaders() })
  },

  async assignTemplateToDevice(deviceId: string, templateId: string) {
    return api.post('/api/v1/device-templates', {
      device_id: deviceId,
      template_id: templateId
    }, { headers: getLicenseHeaders() })
  },

  async removeTemplateFromDevice(deviceId: string) {
    return api.delete(`/api/v1/device-templates/${deviceId}`, { headers: getLicenseHeaders() })
  }
}

// Account device assignments
export const accountDeviceAPI = {
  async getAccountDevices() {
    return api.get('/api/v1/account-devices', undefined, { headers: getLicenseHeaders() })
  },

  async assignDeviceToAccount(accountId: string, deviceId: string) {
    return api.post('/api/v1/account-devices', {
      account_id: accountId,
      device_id: deviceId
    }, { headers: getLicenseHeaders() })
  },

  async removeDeviceFromAccount(accountId: string) {
    return api.delete(`/api/v1/account-devices/${accountId}`, { headers: getLicenseHeaders() })
  }
}

// Log management
export const logAPI = {
  async getLogsForDevice(deviceId: string, params?: { skip?: number; limit?: number }) {
    return api.get(`/api/v1/logs/device/${deviceId}`, params, { headers: getLicenseHeaders() })
  },

  async getLogForDate(deviceId: string, date: string) {
    return api.get(`/api/v1/logs/device/${deviceId}/date/${date}`, undefined, { headers: getLicenseHeaders() })
  },

  async addLogEntry(deviceId: string, date: string, entry: any) {
    return api.post(`/api/v1/logs/device/${deviceId}/date/${date}`, entry, { headers: getLicenseHeaders() })
  },

  async updateLogStatus(deviceId: string, date: string, status: string, endTime?: string) {
    return api.put(`/api/v1/logs/device/${deviceId}/date/${date}`, {
      status,
      end_time: endTime
    }, { headers: getLicenseHeaders() })
  }
}
