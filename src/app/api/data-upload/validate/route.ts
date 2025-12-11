import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const uploadId = searchParams.get('upload_id')

    if (!uploadId) {
      return NextResponse.json(
        { error: 'upload_id parameter is required' },
        { status: 400 }
      )
    }

    const response = await fetch(`${BACKEND_BASE_URL}/api/v1/data/validate?upload_id=${uploadId}`, {
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
    console.error('Validation failed:', error)
    return NextResponse.json(
      { error: 'Failed to validate uploaded data' },
      { status: 500 }
    )
  }
}