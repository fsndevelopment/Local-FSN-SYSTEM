const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://fsn-system-backend.onrender.com"
import { getPlatform } from '@/lib/platform'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async post(endpoint: string, data: any) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Platform": getPlatform(),
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`)
    }

    return response
  }

  async get(endpoint: string, params: URLSearchParams) {
    const response = await fetch(`${this.baseUrl}${endpoint}?${params}`, {
      headers: {
        "X-Platform": getPlatform(),
      },
    })

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`)
    }

    return response.json()
  }
}

const client = new ApiClient(API_BASE_URL)

export async function scanAccount(id: string) {
  const res = await client.post(`/accounts/${id}/scan`, {})
  return res.json()
}

export async function getTrackingSummary(filters: {
  from?: string
  to?: string
  modelIds?: string[]
  accountIds?: string[]
}) {
  const params = new URLSearchParams()
  if (filters.from) params.append("from", filters.from)
  if (filters.to) params.append("to", filters.to)
  if (filters.modelIds) {
    filters.modelIds.forEach((id) => params.append("modelIds[]", id))
  }
  if (filters.accountIds) {
    filters.accountIds.forEach((id) => params.append("accountIds[]", id))
  }

  const response = await client.get(`/tracking/summary`, params)

  return response
}

export async function getTrackingAccounts(filters: {
  from?: string
  to?: string
  modelIds?: string[]
  accountIds?: string[]
}) {
  const params = new URLSearchParams()
  if (filters.from) params.append("from", filters.from)
  if (filters.to) params.append("to", filters.to)
  if (filters.modelIds) {
    filters.modelIds.forEach((id) => params.append("modelIds[]", id))
  }
  if (filters.accountIds) {
    filters.accountIds.forEach((id) => params.append("accountIds[]", id))
  }

  const response = await client.get(`/tracking/accounts`, params)

  return response
}
