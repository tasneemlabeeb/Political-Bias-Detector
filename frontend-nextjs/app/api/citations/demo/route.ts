import { NextResponse } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'
const BACKEND_INTERNAL = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000/api'

async function getBackendUrl() {
  // Server-side: use internal Docker network URL
  // The NEXT_PUBLIC_ var has the external URL, but server-side we need internal
  return BACKEND_INTERNAL
}

export async function POST() {
  try {
    const backendUrl = await getBackendUrl()
    const res = await fetch(`${backendUrl}/v1/citations/demo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error creating demo network:', error)
    return NextResponse.json(
      { error: 'Failed to create demo network' },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    const backendUrl = await getBackendUrl()

    // Fetch all data in parallel from the backend
    const [summaryRes, sourcesRes, chambersRes, crossBiasRes] = await Promise.all([
      fetch(`${backendUrl}/v1/citations/summary`),
      fetch(`${backendUrl}/v1/citations/sources?sort_by=authority`),
      fetch(`${backendUrl}/v1/citations/echo-chambers`),
      fetch(`${backendUrl}/v1/citations/cross-bias`),
    ])

    const summary = await summaryRes.json()
    const sources = await sourcesRes.json()
    const echoChambers = await chambersRes.json()
    const crossBias = await crossBiasRes.json()

    // If network is empty, return null summary so frontend shows empty state
    if (summary.total_sources === 0) {
      return NextResponse.json({
        summary: null,
        sources: [],
        echoChambers: [],
        crossBias: null,
      })
    }

    return NextResponse.json({
      summary,
      sources,
      echoChambers,
      crossBias,
    })
  } catch (error) {
    console.error('Error loading network data:', error)
    return NextResponse.json({
      summary: null,
      sources: [],
      echoChambers: [],
      crossBias: null,
    })
  }
}
