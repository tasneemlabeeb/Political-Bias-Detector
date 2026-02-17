import { NextRequest, NextResponse } from 'next/server'

const BACKEND_INTERNAL = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000/api'

export async function GET(request: NextRequest) {
  try {
    const sortBy = request.nextUrl.searchParams.get('sort_by') || 'authority'
    const res = await fetch(`${BACKEND_INTERNAL}/v1/citations/sources?sort_by=${sortBy}`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json([])
  }
}
