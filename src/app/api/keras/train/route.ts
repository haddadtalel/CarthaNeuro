import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { model_name, model_type, epochs, batch_size, validation_split, learning_rate } = body

    // Validate required parameters
    if (!model_name || !model_type || !epochs || !batch_size || !validation_split || !learning_rate) {
      return NextResponse.json(
        { error: 'Missing required training parameters' }, 
        { status: 400 }
      )
    }

    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.trainKerasModel({
      model_name,
      model_type,
      epochs,
      batch_size,
      validation_split,
      learning_rate
    })

    if (!response.success) {
      return NextResponse.json(
        { error: response.error || 'Keras training request failed' }, 
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Keras model training started successfully',
      model_name,
      model_type,
      parameters: {
        epochs,
        batch_size,
        validation_split,
        learning_rate
      },
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Keras training proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}