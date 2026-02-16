import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json()
  
  // In production, this would call the FastAPI backend
  // For now, return mock data
  
  return NextResponse.json({
    source_url: body.video_url,
    source_type: 'youtube',
    title: 'Sample Video',
    duration: 0,
    transcript: '',
    timestamp: new Date().toISOString(),
    political_bias: null,
    ml_confidence: null,
    ml_explanation: null,
    bias_timeline: null,
    segments: null
  })
}
