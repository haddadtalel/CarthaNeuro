import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

export async function GET() {
  try {
    // Get latest model metrics
    const latestMetrics = await prisma.modelMetrics.findFirst({
      orderBy: { createdAt: 'desc' }
    })

    if (!latestMetrics) {
      // Return mock data if no metrics exist
      return NextResponse.json({
        accuracy: 0.94,
        precision: 0.91,
        recall: 0.89,
        f1Score: 0.90,
        trainingLoss: 0.12,
        validationLoss: 0.15,
        timestamp: new Date().toISOString()
      })
    }

    return NextResponse.json({
      accuracy: latestMetrics.accuracy,
      precision: latestMetrics.precision,
      recall: latestMetrics.recall,
      f1Score: latestMetrics.f1Score,
      trainingLoss: latestMetrics.trainingLoss,
      validationLoss: latestMetrics.validationLoss,
      timestamp: latestMetrics.createdAt
    })

  } catch (error) {
    console.error('KPI fetch error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}