'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp, Filter } from 'lucide-react'
import { Article, FilterState, BIAS_ORDER } from '@/types'

interface Props {
  articles: Article[]
  filters: FilterState
  setFilters: (filters: FilterState) => void
  mlEnabled: boolean
}

export default function FilterPanel({ articles, filters, setFilters, mlEnabled }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  const availableSources = Array.from(new Set(articles.map(a => a.source_name))).sort()
  const availableBiases = BIAS_ORDER.filter(bias =>
    articles.some(a => (a.political_bias || a.ml_bias) === bias)
  )

  return (
    <div className="mb-8">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full card p-4 flex items-center justify-between hover:shadow-md transition-all group"
      >
        <div className="flex items-center gap-3">
          <Filter className="w-5 h-5 text-[#142c4c]" />
          <span className="font-bold text-lg">Filters & Sorting</span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-[var(--muted)] group-hover:text-[#142c4c] transition-colors" />
        ) : (
          <ChevronDown className="w-5 h-5 text-[var(--muted)] group-hover:text-[#142c4c] transition-colors" />
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="card p-6 mt-2">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                {/* Sources */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                    Source
                  </label>
                  <select
                    multiple
                    value={filters.sources}
                    onChange={(e) => {
                      const values = Array.from(e.target.selectedOptions, option => option.value)
                      setFilters({ ...filters, sources: values })
                    }}
                    className="w-full border border-[var(--line)] p-2 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
                    size={4}
                  >
                    {availableSources.map(source => (
                      <option key={source} value={source}>
                        {source}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Biases */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                    Political Bias
                  </label>
                  <div className="space-y-2">
                    {availableBiases.map(bias => (
                      <label key={bias} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={filters.biases.includes(bias)}
                          onChange={(e) => {
                            const newBiases = e.target.checked
                              ? [...filters.biases, bias]
                              : filters.biases.filter(b => b !== bias)
                            setFilters({ ...filters, biases: newBiases })
                          }}
                          className="w-4 h-4"
                        />
                        {bias}
                      </label>
                    ))}
                  </div>
                </div>

                {/* Date Range */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                    From
                  </label>
                  <input
                    type="date"
                    value={filters.dateFrom.toISOString().split('T')[0]}
                    onChange={(e) =>
                      setFilters({ ...filters, dateFrom: new Date(e.target.value) })
                    }
                    className="w-full border border-[var(--line)] p-2 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
                  />
                  <label className="block text-sm font-semibold mb-2 mt-3 text-[var(--ink)]">
                    To
                  </label>
                  <input
                    type="date"
                    value={filters.dateTo.toISOString().split('T')[0]}
                    onChange={(e) =>
                      setFilters({ ...filters, dateTo: new Date(e.target.value) })
                    }
                    className="w-full border border-[var(--line)] p-2 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
                  />
                </div>

                {/* Sort */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                    Sort By
                  </label>
                  <select
                    value={filters.sortBy}
                    onChange={(e) =>
                      setFilters({ ...filters, sortBy: e.target.value as any })
                    }
                    className="w-full border border-[var(--line)] p-2 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
                  >
                    <option value="date-desc">Date (newest first)</option>
                    <option value="date-asc">Date (oldest first)</option>
                    <option value="source">Source (A-Z)</option>
                    {mlEnabled && <option value="confidence">AI Confidence</option>}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Keyword Search */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                    Keyword Search
                  </label>
                  <input
                    type="text"
                    placeholder="Search title, summary, and content..."
                    value={filters.keyword}
                    onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
                    className="w-full border border-[var(--line)] p-2 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
                  />
                </div>

                {/* AI Confidence Slider */}
                {mlEnabled && (
                  <div>
                    <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                      Minimum AI Confidence: {filters.minConfidence}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={filters.minConfidence}
                      onChange={(e) =>
                        setFilters({ ...filters, minConfidence: parseInt(e.target.value) })
                      }
                      className="w-full"
                    />
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
