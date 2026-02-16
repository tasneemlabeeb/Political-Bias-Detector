import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json()
  
  // In production, this would call the FastAPI backend
  // For now, return mock data
  
  return NextResponse.json({
    subreddit: body.subreddit,
    posts_count: 0,
    post_bias_distribution: {},
    comments_count: 0,
    comment_bias_distribution: {},
    avg_confidence: 0,
    posts: [],
    comments: []
  })
}
