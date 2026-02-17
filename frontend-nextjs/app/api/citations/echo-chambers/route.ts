import { NextResponse } from 'next/server'

const BACKEND_INTERNAL = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000/api'

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_INTERNAL}/v1/citations/echo-chambers`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json([])
  }
}
