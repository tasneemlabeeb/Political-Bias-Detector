import { NextResponse } from 'next/server'

export async function GET() {
  // In production, this would call the FastAPI backend
  // For now, return empty data
  
  return NextResponse.json({
    cross_bias_matrix: {},
    total_cross_bias_citations: 0,
    total_same_bias_citations: 0
  })
}
