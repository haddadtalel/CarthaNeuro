import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const model_path = formData.get('model_path') as string
    const model_name = formData.get('model_name') as string

    if (!model_path) {
      return NextResponse.json(
        { error: 'Missing required parameter: model_path' }, 
        { status: 400 }
      )
    }

    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.loadKerasModel(model_path, model_name)

    if (!response.success) {
      return NextResponse.json(
        { error: response.error || 'Failed to load Keras model' }, 
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Keras model loaded successfully',
      model_name: response.result?.model_name,
      model_type: response.result?.model_type,
      model_info: response.result?.model_info,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Keras load proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}