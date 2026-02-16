import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { articles } = await request.json()

  // TODO: Call your Python backend API for classification
  // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/classify`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ articles }),
  // })
  // const data = await response.json()

  // Mock response for now
  const classifiedArticles = articles.map((article: any) => ({
    ...article,
    ml_bias: 'Center-Left',
    ml_confidence: 0.85,
    ml_explanation: 'This is a sample AI classification result.',
  }))

  return NextResponse.json(classifiedArticles)
}
