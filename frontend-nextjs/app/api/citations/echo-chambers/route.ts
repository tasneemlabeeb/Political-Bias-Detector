import { NextResponse } from 'next/server'

export async function GET() {
  // In production, this would call the FastAPI backend
  // For now, return empty data
  
  return NextResponse.json([])
}
