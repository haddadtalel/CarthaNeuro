import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

export async function GET() {
  try {
    const datasets = await prisma.dataset.findMany({
      orderBy: { createdAt: 'desc' }
    })

    return NextResponse.json(datasets)

  } catch (error) {
    console.error('Datasets fetch error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const userId = formData.get('userId') as string
    const name = formData.get('name') as string

    if (!file || !userId || !name) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // Mock dataset analysis (replace with actual processing)
    const sampleCount = Math.floor(Math.random() * 1000) + 500
    const classCount = Math.floor(Math.random() * 3) + 2

    const dataset = await prisma.dataset.create({
      data: {
        userId,
        name,
        fileUrl: '/uploads/datasets/' + file.name, // Mock URL
        fileSize: file.size,
        sampleCount,
        classCount
      }
    })

    return NextResponse.json(dataset)

  } catch (error) {
    console.error('Dataset upload error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}