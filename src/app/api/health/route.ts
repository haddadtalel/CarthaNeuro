import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/v1/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Health check failed:', error)
    return NextResponse.json(
      { 
        error: 'Failed to connect to backend',
        status: 'unhealthy',
        timestamp: Date.now()
      },
      { status: 500 }
    )
  }
}