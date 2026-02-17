import { NextResponse } from 'next/server'

const BACKEND_INTERNAL = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000/api'

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_INTERNAL}/v1/citations/summary`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({
      total_sources: 0,
      total_citations: 0,
      avg_citations_per_source: 0,
      most_cited: [],
      most_citing: [],
      avg_echo_chamber_score: 0,
      network_density: 0,
    })
  }
}
