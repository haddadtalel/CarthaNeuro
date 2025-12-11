import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('image') as File
    const model_name = formData.get('model_name') as string

    if (!file || !model_name) {
      return NextResponse.json(
        { error: 'Missing required parameters: image and model_name' }, 
        { status: 400 }
      )
    }

    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.kerasPredict(file, model_name)

    if (!response.success) {
      return NextResponse.json(
        { error: response.error || 'Keras prediction failed' }, 
        { status: 500 }
      )
    }

    // Transform the backend response to frontend format
    const result = response.result
    const classification = result?.classification?.prediction
    
    return NextResponse.json({
      id: `keras_pred_${Date.now()}`,
      disease: classification?.class || 'Unknown',
      confidence: classification?.confidence || 0,
      fullResult: result, // Include full result for detailed analysis
      model_name,
      processingTime: response.processing_time,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Keras prediction proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}