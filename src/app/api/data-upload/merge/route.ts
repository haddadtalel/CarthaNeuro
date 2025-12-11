import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const uploadId = searchParams.get('upload_id')
    const datasetName = searchParams.get('dataset_name')

    if (!uploadId || !datasetName) {
      return NextResponse.json(
        { error: 'upload_id and dataset_name parameters are required' },
        { status: 400 }
      )
    }

    const response = await fetch(`${BACKEND_BASE_URL}/api/v1/data/merge?upload_id=${uploadId}&dataset_name=${datasetName}`, {
      method: 'POST',
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
    console.error('Merge failed:', error)
    return NextResponse.json(
      { 
        success: false,
        message: 'Failed to merge dataset',
        timestamp: Date.now()
      },
      { status: 500 }
    )
  }
}