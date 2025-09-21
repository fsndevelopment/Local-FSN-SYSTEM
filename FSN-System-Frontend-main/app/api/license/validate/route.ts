// @ts-ignore
import { NextRequest, NextResponse } from 'next/server'

interface LicenseValidationRequest {
  license_key: string
  device_id: string
}

interface LicenseValidationResponse {
  valid: boolean
  error?: string
  platforms?: string[]
  license_type?: string
  expires_at?: string
  max_devices?: number
  current_devices?: number
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body: LicenseValidationRequest = await request.json()
    const { license_key, device_id } = body

    if (!license_key || !device_id) {
      return NextResponse.json(
        { error: 'License key and device ID are required' },
        { status: 400 }
      )
    }

    // Call the license server from the server side (no CORS issues)
    // @ts-ignore
    const licenseServerUrl = process.env.LICENSE_SERVER_URL || 'https://fsn-system-license.onrender.com'
    
    const response = await fetch(`${licenseServerUrl}/api/v1/license/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        license_key: license_key.trim(),
        device_id: device_id.trim(),
      }),
    })

    const data: LicenseValidationResponse = await response.json()

    // Return the response with proper CORS headers
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
  } catch (error) {
    console.error('License validation proxy error:', error)
    
    // If it's a timeout or network error, return a more graceful response
    // instead of causing a logout
    if (error instanceof Error && (error.name === 'AbortError' || error.message.includes('timeout') || error.message.includes('fetch failed'))) {
      console.warn('License server timeout - allowing local development mode')
      return NextResponse.json(
        { 
          valid: true, // Allow access during server issues
          error: 'License server temporarily unavailable - local development mode', 
          license_type: 'development',
          platforms: ['iOS', 'Android']
        },
        { status: 200 }
      )
    }
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function OPTIONS(): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}