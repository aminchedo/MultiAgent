import { NextResponse } from 'next/server'

export async function POST() {
  return NextResponse.json({
    status: 'connected',
    provider: 'mock',
    latency: Math.floor(Math.random() * 80) + 20,
    timestamp: new Date().toISOString()
  })
}