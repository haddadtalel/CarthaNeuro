import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { model_name, save_path, metadata } = body

    // Validate required parameters
    if (!model_name) {
      return NextResponse.json(
        { error: 'Missing required parameter: model_name' }, 
        { status: 400 }
      )
    }

    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.saveKerasModel({
      model_name,
      save_path,
      metadata
    })

    if (!response.success) {
      return NextResponse.json(
        { error: response.error || 'Failed to save Keras model' }, 
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Keras model saved successfully',
      model_name,
      model_path: response.result?.model_path,
      files: response.result?.files,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Keras save proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}