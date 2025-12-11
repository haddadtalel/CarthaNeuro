import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { model_types } = body

    // Call the actual FastAPI backend
    await CarthaNeuroApi.reloadModels(model_types)

    return NextResponse.json({
      success: true,
      message: 'Models reloaded successfully',
      model_types,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Models reload proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}