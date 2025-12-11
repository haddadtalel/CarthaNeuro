import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function GET(request: NextRequest) {
  try {
    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.getKerasModels()

    return NextResponse.json({
      success: true,
      models: response.models,
      total: response.models.length,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Keras models proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}