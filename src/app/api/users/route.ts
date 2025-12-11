import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

export async function GET() {
  try {
    const users = await prisma.user.findMany({
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        createdAt: true,
        _count: {
          select: { predictions: true }
        }
      },
      orderBy: { createdAt: 'desc' }
    })

    const formattedUsers = users.map(user => ({
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      analysesCount: user._count.predictions,
      createdAt: user.createdAt
    }))

    return NextResponse.json(formattedUsers)

  } catch (error) {
    console.error('Users fetch error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}