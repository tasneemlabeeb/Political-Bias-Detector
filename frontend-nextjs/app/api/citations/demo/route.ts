import { NextResponse } from 'next/server'

// Demo network with sample data
const demoData = {
  summary: {
    total_sources: 8,
    total_citations: 13,
    avg_citations_per_source: 1.625,
    most_cited: [
      ['CNN', 3],
      ['Fox News', 3],
      ['New York Times', 2],
      ['NPR', 2],
      ['Wall Street Journal', 2]
    ],
    most_citing: [
      ['CNN', 2],
      ['Fox News', 2],
      ['New York Times', 2],
      ['NPR', 2],
      ['Reuters', 2]
    ],
    avg_echo_chamber_score: 0.62,
    network_density: 0.23
  },
  sources: [
    { name: 'CNN', domain: 'cnn.com', political_bias: 'left', citations_made: 2, citations_received: 3, authority_score: 0.15, echo_chamber_score: 0.67, same_bias_citations: 2, different_bias_citations: 0 },
    { name: 'Fox News', domain: 'foxnews.com', political_bias: 'right', citations_made: 2, citations_received: 3, authority_score: 0.15, echo_chamber_score: 0.67, same_bias_citations: 2, different_bias_citations: 0 },
    { name: 'New York Times', domain: 'nytimes.com', political_bias: 'left_leaning', citations_made: 2, citations_received: 2, authority_score: 0.13, echo_chamber_score: 0.5, same_bias_citations: 1, different_bias_citations: 1 },
    { name: 'Wall Street Journal', domain: 'wsj.com', political_bias: 'right_leaning', citations_made: 1, citations_received: 2, authority_score: 0.11, echo_chamber_score: 1.0, same_bias_citations: 1, different_bias_citations: 0 },
    { name: 'Reuters', domain: 'reuters.com', political_bias: 'center', citations_made: 2, citations_received: 0, authority_score: 0.09, echo_chamber_score: 0, same_bias_citations: 0, different_bias_citations: 2 },
    { name: 'MSNBC', domain: 'msnbc.com', political_bias: 'left', citations_made: 1, citations_received: 1, authority_score: 0.08, echo_chamber_score: 1.0, same_bias_citations: 1, different_bias_citations: 0 },
    { name: 'Breitbart', domain: 'breitbart.com', political_bias: 'right', citations_made: 1, citations_received: 1, authority_score: 0.08, echo_chamber_score: 1.0, same_bias_citations: 1, different_bias_citations: 0 },
    { name: 'NPR', domain: 'npr.org', political_bias: 'center', citations_made: 2, citations_received: 2, authority_score: 0.13, echo_chamber_score: 0, same_bias_citations: 0, different_bias_citations: 2 }
  ],
  echoChambers: [
    {
      chamber_id: 0,
      sources: ['CNN', 'New York Times', 'MSNBC'],
      dominant_bias: 'left',
      internal_citations: 4,
      external_citations: 1,
      insularity_score: 0.80,
      avg_authority: 0.12
    },
    {
      chamber_id: 1,
      sources: ['Fox News', 'Breitbart', 'Wall Street Journal'],
      dominant_bias: 'right',
      internal_citations: 4,
      external_citations: 0,
      insularity_score: 1.0,
      avg_authority: 0.11
    }
  ],
  crossBias: {
    cross_bias_matrix: {
      left: { left: 2, left_leaning: 1, center: 0, right_leaning: 0, right: 0 },
      left_leaning: { left: 1, left_leaning: 0, center: 1, right_leaning: 0, right: 0 },
      center: { left: 1, left_leaning: 1, center: 0, right_leaning: 1, right: 1 },
      right_leaning: { left: 0, left_leaning: 0, center: 0, right_leaning: 0, right: 1 },
      right: { left: 0, left_leaning: 0, center: 0, right_leaning: 1, right: 1 }
    },
    total_cross_bias_citations: 6,
    total_same_bias_citations: 7
  }
}

export async function POST() {
  // Return demo network data
  return NextResponse.json({
    status: 'success',
    message: 'Demo network created',
    sources: 8,
    citations: 13,
    summary: demoData.summary
  })
}

// Also handle GET to return if demo exists
export async function GET() {
  return NextResponse.json(demoData)
}
