import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function DELETE(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/v1/data/cleanup`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || `Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Cleanup failed:', error)
    return NextResponse.json(
      { 
        success: false,
        message: error instanceof Error ? error.message : 'Cleanup failed',
        timestamp: Date.now()
      },
      { status: 500 }
    )
  }
}