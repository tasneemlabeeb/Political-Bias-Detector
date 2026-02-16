'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Network, TrendingUp, AlertCircle, Users } from 'lucide-react'

export default function CitationsPage() {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<any>(null)
  const [echoChambers, setEchoChambers] = useState<any[]>([])
  const [sources, setSources] = useState<any[]>([])
  const [crossBias, setCrossBias] = useState<any>(null)

  useEffect(() => {
    loadNetworkData()
  }, [])

  const loadNetworkData = async () => {
    setLoading(true)
    try {
      // Check if demo data exists
      const demoRes = await fetch('/api/citations/demo')
      const demoData = await demoRes.json()
      
      if (demoData.summary) {
        setSummary(demoData.summary)
        setEchoChambers(demoData.echoChambers || [])
        setSources(demoData.sources || [])
        setCrossBias(demoData.crossBias || null)
      } else {
        // Load from individual endpoints
        const summaryRes = await fetch('/api/citations/summary')
        const summaryData = await summaryRes.json()
        setSummary(summaryData)

        const chambersRes = await fetch('/api/citations/echo-chambers')
        const chambersData = await chambersRes.json()
        setEchoChambers(chambersData)

        const sourcesRes = await fetch('/api/citations/sources?sort_by=authority')
        const sourcesData = await sourcesRes.json()
        setSources(sourcesData)

        const crossBiasRes = await fetch('/api/citations/cross-bias')
        const crossBiasData = await crossBiasRes.json()
        setCrossBias(crossBiasData)
      }
    } catch (error) {
      console.error('Error loading network data:', error)
    }
    setLoading(false)
  }

  const createDemoNetwork = async () => {
    setLoading(true)
    try {
      await fetch('/api/citations/demo', { method: 'POST' })
      await loadNetworkData()
    } catch (error) {
      console.error('Error creating demo network:', error)
    }
    setLoading(false)
  }

  const biasColors: Record<string, string> = {
    left: '#1565C0',
    left_leaning: '#42A5F5',
    center: '#9E9E9E',
    right_leaning: '#EF5350',
    right: '#C62828'
  }

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-[var(--ink)] mb-2">
            Citation Network Analysis
          </h1>
          <p className="text-[var(--muted)]">
            Discover how news sources cite each other and identify echo chambers
          </p>
        </motion.div>

        {/* Actions */}
        <div className="card p-6 mb-8">
          <div className="flex gap-4">
            <button
              onClick={createDemoNetwork}
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              <Network className="w-5 h-5 inline-block mr-2" />
              Create Demo Network
            </button>
            <button
              onClick={loadNetworkData}
              disabled={loading}
              className="btn-secondary disabled:opacity-50"
            >
              Refresh Data
            </button>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="text-[var(--muted)]">Loading network data...</div>
          </div>
        )}

        {!loading && summary && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {summary.total_sources}
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  News Sources
                </div>
              </div>
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {summary.total_citations}
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Total Citations
                </div>
              </div>
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {summary.avg_citations_per_source.toFixed(1)}
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Avg Citations/Source
                </div>
              </div>
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {(summary.avg_echo_chamber_score * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Echo Chamber Score
                </div>
              </div>
            </div>

            {/* Most Cited Sources */}
            <div className="card p-6">
              <h3 className="text-xl font-bold text-[var(--ink)] mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Most Cited Sources
              </h3>
              <div className="space-y-3">
                {summary.most_cited?.map(([source, count]: [string, number], idx: number) => (
                  <div key={source} className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-[#142c4c] text-white flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div className="flex-1 font-semibold">{source}</div>
                    <div className="flex-1 h-6 bg-gray-200 relative">
                      <div
                        className="h-full bg-[#142c4c] flex items-center px-2 text-white text-xs font-bold"
                        style={{
                          width: `${(count / summary.most_cited[0][1]) * 100}%`
                        }}
                      >
                        {count}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Echo Chambers */}
            {echoChambers.length > 0 && (
              <div className="card p-6">
                <h3 className="text-xl font-bold text-[var(--ink)] mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  Echo Chambers Detected
                </h3>
                <div className="space-y-4">
                  {echoChambers.map((chamber) => (
                    <div
                      key={chamber.chamber_id}
                      className="border border-gray-200 p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="font-bold text-lg mb-1">
                            Chamber #{chamber.chamber_id + 1}
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className="px-3 py-1 text-white text-xs font-bold"
                              style={{
                                backgroundColor: biasColors[chamber.dominant_bias] || '#142c4c'
                              }}
                            >
                              {chamber.dominant_bias}
                            </span>
                            <span className="text-sm text-[var(--muted)]">
                              {chamber.sources.length} sources
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-[var(--ink)]">
                            {(chamber.insularity_score * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-[var(--muted)]">
                            Insularity
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-3">
                        {chamber.sources.map((source: string) => (
                          <span
                            key={source}
                            className="px-2 py-1 bg-gray-100 text-xs font-semibold border border-gray-200"
                          >
                            {source}
                          </span>
                        ))}
                      </div>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-[var(--muted)]">Internal Citations:</span>
                          <span className="font-bold ml-2">{chamber.internal_citations}</span>
                        </div>
                        <div>
                          <span className="text-[var(--muted)]">External Citations:</span>
                          <span className="font-bold ml-2">{chamber.external_citations}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Cross-Bias Citation Matrix */}
            {crossBias && (
              <div className="card p-6">
                <h3 className="text-xl font-bold text-[var(--ink)] mb-4">
                  Cross-Bias Citation Patterns
                </h3>
                <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-green-50 border border-green-200 p-3">
                    <div className="text-green-900 font-semibold mb-1">
                      Cross-Bias Citations
                    </div>
                    <div className="text-2xl font-bold text-green-900">
                      {crossBias.total_cross_bias_citations}
                    </div>
                  </div>
                  <div className="bg-orange-50 border border-orange-200 p-3">
                    <div className="text-orange-900 font-semibold mb-1">
                      Same-Bias Citations
                    </div>
                    <div className="text-2xl font-bold text-orange-900">
                      {crossBias.total_same_bias_citations}
                    </div>
                  </div>
                </div>

                {crossBias.cross_bias_matrix && (
                  <div className="overflow-x-auto">
                    <div className="text-xs text-[var(--muted)] mb-2">
                      Matrix shows citations FROM (rows) TO (columns)
                    </div>
                    <table className="w-full text-sm">
                      <thead>
                        <tr>
                          <th className="p-2 border border-gray-200 bg-gray-50"></th>
                          {Object.keys(crossBias.cross_bias_matrix).map((bias) => (
                            <th
                              key={bias}
                              className="p-2 border border-gray-200 bg-gray-50 font-bold"
                            >
                              {bias.replace('_', ' ')}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(crossBias.cross_bias_matrix).map(
                          ([fromBias, toCounts]: [string, any]) => (
                            <tr key={fromBias}>
                              <td className="p-2 border border-gray-200 bg-gray-50 font-bold">
                                {fromBias.replace('_', ' ')}
                              </td>
                              {Object.entries(toCounts).map(([toBias, count]: [string, any]) => (
                                <td
                                  key={toBias}
                                  className="p-2 border border-gray-200 text-center font-semibold"
                                  style={{
                                    backgroundColor:
                                      count > 0
                                        ? `rgba(20, 44, 76, ${Math.min(count / 10, 1) * 0.5})`
                                        : 'white'
                                  }}
                                >
                                  {count || '-'}
                                </td>
                              ))}
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* All Sources */}
            {sources.length > 0 && (
              <div className="card p-6">
                <h3 className="text-xl font-bold text-[var(--ink)] mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  All Sources
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left p-3 font-bold">Source</th>
                        <th className="text-left p-3 font-bold">Bias</th>
                        <th className="text-center p-3 font-bold">Authority</th>
                        <th className="text-center p-3 font-bold">Cited</th>
                        <th className="text-center p-3 font-bold">Cites</th>
                        <th className="text-center p-3 font-bold">Echo Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sources.map((source) => (
                        <tr key={source.name} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="p-3 font-semibold">{source.name}</td>
                          <td className="p-3">
                            {source.political_bias && (
                              <span
                                className="px-2 py-1 text-white text-xs font-bold"
                                style={{
                                  backgroundColor: biasColors[source.political_bias] || '#142c4c'
                                }}
                              >
                                {source.political_bias}
                              </span>
                            )}
                          </td>
                          <td className="p-3 text-center">
                            {(source.authority_score * 100).toFixed(1)}
                          </td>
                          <td className="p-3 text-center font-semibold">
                            {source.citations_received}
                          </td>
                          <td className="p-3 text-center font-semibold">
                            {source.citations_made}
                          </td>
                          <td className="p-3 text-center">
                            {(source.echo_chamber_score * 100).toFixed(0)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !summary && (
          <div className="card p-12 text-center">
            <Network className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-bold text-[var(--ink)] mb-2">
              No Network Data Available
            </h3>
            <p className="text-[var(--muted)] mb-6">
              Create a demo network to see how citation analysis works
            </p>
            <button onClick={createDemoNetwork} className="btn-primary">
              Create Demo Network
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
