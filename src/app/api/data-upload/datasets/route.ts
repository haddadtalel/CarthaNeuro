import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/v1/data/datasets`, {
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
    console.error('Failed to list datasets:', error)
    return NextResponse.json(
      { error: 'Failed to fetch datasets' },
      { status: 500 }
    )
  }
}