import { NextResponse } from 'next/server'

// Mock data for development
// In production, this would fetch from your Python backend
export async function GET() {
  const mockArticles = [
    {
      id: '1',
      title: 'Sample Political Article',
      link: 'https://example.com',
      summary: 'This is a sample article for demonstration purposes.',
      published: new Date().toISOString(),
      source_name: 'BBC News',
      political_bias: 'Centrist' as const,
    },
  ]

  return NextResponse.json(mockArticles)
}
