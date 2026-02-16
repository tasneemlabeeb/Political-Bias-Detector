import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json()
  
  // In production, this would call the FastAPI backend
  // For now, return mock data
  
  return NextResponse.json({
    query: body.query,
    posts_count: 0,
    bias_distribution: {},
    hashtag_bias: {},
    avg_confidence: 0,
    posts: []
  })
}
