import { NextResponse } from 'next/server'

export async function GET() {
  // In production, this would call the FastAPI backend
  // For now, return empty data
  
  return NextResponse.json({
    total_sources: 0,
    total_citations: 0,
    avg_citations_per_source: 0,
    most_cited: [],
    most_citing: [],
    cross_bias_matrix: {},
    avg_echo_chamber_score: 0,
    network_density: 0
  })
}
