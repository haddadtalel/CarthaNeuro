import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const userId = formData.get('userId') as string
    const patientContext = formData.get('patientContext') as string || ''
    const modelType = (formData.get('modelType') as string) || '3d_cnn'
    const modelName = (formData.get('modelName') as string) || 'real' // Default to 'real' model
    const useLlm = (formData.get('useLlm') as string) === 'true'

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 })
    }

    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.predict({
      image: file,
      patientContext,
      modelType: modelType as '3d_cnn' | '3d_vit',
      modelName, // Pass the model name to ensure 'real' model is used
      useLlm
    })

    if (!response.success) {
      return NextResponse.json(
        { error: response.error || 'Prediction failed' }, 
        { status: 500 }
      )
    }

    // Transform the backend response to frontend format
    const result = response.result
    const prediction = result?.prediction
    
    return NextResponse.json({
      id: `pred_${Date.now()}`,
      disease: prediction?.class || 'Unknown',
      confidence: prediction?.confidence || 0,
      fullResult: result, // Include full result for detailed analysis
      processingTime: response.processing_time,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Prediction proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}