import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  // In production, this would handle file upload and call the FastAPI backend
  // For now, return mock data
  
  return NextResponse.json({
    source_url: null,
    source_type: 'audio',
    title: 'Uploaded File',
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
