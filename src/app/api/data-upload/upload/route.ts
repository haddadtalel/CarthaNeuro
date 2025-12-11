import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    
    // Get the authorization header from the incoming request
    const authHeader = request.headers.get('Authorization')
    // Also check for token in cookies (set by auth-service)
    const tokenFromCookie = request.cookies.get('access_token')?.value
    
    const headers: HeadersInit = {}
    if (authHeader) {
      headers['Authorization'] = authHeader
    } else if (tokenFromCookie) {
      headers['Authorization'] = `Bearer ${tokenFromCookie}`
    }
    
    const response = await fetch(`${BACKEND_BASE_URL}/api/v1/data/upload`, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || errorData.detail || `Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Upload failed:', error)
    return NextResponse.json(
      { 
        success: false,
        message: error instanceof Error ? error.message : 'Upload failed',
        timestamp: Date.now()
      },
      { status: 500 }
    )
  }
}