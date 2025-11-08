import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const userId = formData.get('userId') as string

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 })
    }

    // Mock AI prediction (replace with actual model inference)
    const diseases = ['Alzheimer\'s', 'Parkinson\'s', 'Healthy']
    const randomDisease = diseases[Math.floor(Math.random() * diseases.length)]
    const confidence = Math.random() * 0.3 + 0.7 // 0.7 to 1.0

    // Save prediction to database
    const prediction = await prisma.prediction.create({
      data: {
        userId: userId || 'anonymous',
        imageUrl: '/uploads/' + file.name, // Mock URL
        disease: randomDisease,
        confidence: confidence,
        modelVersion: 'v2.1'
      }
    })

    return NextResponse.json({
      id: prediction.id,
      disease: prediction.disease,
      confidence: prediction.confidence,
      heatmapUrl: '/heatmaps/' + prediction.id + '.png', // Mock heatmap
      timestamp: prediction.createdAt
    })

  } catch (error) {
    console.error('Prediction error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}