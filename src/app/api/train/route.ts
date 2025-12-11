import { NextRequest, NextResponse } from 'next/server'
import { CarthaNeuroApi } from '@/lib/api'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { modelType, architecture, numEpochs, batchSize, learningRate, validationSplit, device } = body

    // Validate required parameters
    if (!modelType || !architecture || !numEpochs || !batchSize || !learningRate || !validationSplit) {
      return NextResponse.json(
        { error: 'Missing required training parameters' }, 
        { status: 400 }
      )
    }

    // Call the actual FastAPI backend
    const response = await CarthaNeuroApi.trainModel({
      model_type: modelType,
      architecture,
      num_epochs: numEpochs,
      batch_size: batchSize,
      learning_rate: learningRate,
      validation_split: validationSplit,
      device: device || 'cpu'  // Default to CPU if not specified
    })

    if (!response.success) {
      return NextResponse.json(
        { error: response.error || 'Training request failed' }, 
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: 'Model training started successfully',
      parameters: {
        model_type: modelType,
        architecture,
        num_epochs: numEpochs,
        batch_size: batchSize,
        learning_rate: learningRate,
        validation_split: validationSplit,
        device: device || 'cpu'
      },
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Training proxy error:', error)
    
    // Handle API connection errors gracefully
    if (error instanceof Error && error.message.includes('Unable to connect to backend')) {
      return NextResponse.json({ 
        error: 'Backend service is unavailable. Please ensure the CarthaNeuro backend is running.' 
      }, { status: 503 })
    }
    
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}