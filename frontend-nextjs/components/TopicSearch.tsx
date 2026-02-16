'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface TopicSearchProps {
  onSearch: (topic: string) => void
  loading: boolean
}

export default function TopicSearch({ onSearch, loading }: TopicSearchProps) {
  const [topic, setTopic] = useState('')
  const [showInfo, setShowInfo] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (topic.trim().length >= 3) {
      onSearch(topic.trim())
    }
  }

  return (
    <div className="mb-8">
      <div className="bg-white border-2 border-[var(--line)] p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-[#142c4c] mb-1">
              AI-Powered Topic Search
            </h2>
            <p className="text-sm text-[var(--muted)]">
              Enter any topic and our LLM will find relevant news across all sources
            </p>
          </div>
          <button
            onClick={() => setShowInfo(!showInfo)}
            className="text-[#142c4c] hover:text-[var(--muted)] transition-colors"
            aria-label="Toggle info"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>

        <AnimatePresence>
          {showInfo && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mb-4 p-4 bg-[#f8f9fa] border-l-4 border-[#142c4c] overflow-hidden"
            >
              <p className="text-sm text-[var(--muted)] leading-relaxed">
                <strong>How it works:</strong>
                <br />
                1. LLM generates diverse search queries from your topic
                <br />
                2. Crawls news from all active sources
                <br />
                3. Ranks articles by relevance
                <br />
                4. ML analyzes each article for political bias
                <br />
                5. Returns results with bias classification and confidence scores
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="flex-1">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter a topic (e.g., 'climate policy', 'healthcare reform', 'immigration')"
              className="w-full px-4 py-3 border-2 border-[var(--line)] focus:border-[#142c4c] focus:outline-none transition-colors"
              minLength={3}
              maxLength={200}
              disabled={loading}
            />
            {topic.length > 0 && topic.length < 3 && (
              <p className="text-xs text-red-600 mt-1">Topic must be at least 3 characters</p>
            )}
          </div>
          <button
            type="submit"
            disabled={loading || topic.trim().length < 3}
            className="px-8 py-3 bg-[#142c4c] text-white font-semibold hover:bg-opacity-90 disabled:bg-[var(--muted)] disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Searching...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search
              </span>
            )}
          </button>
        </form>

        {loading && (
          <div className="mt-4 flex items-center gap-2 text-sm text-[var(--muted)]">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            LLM analyzing topic and generating search queries...
          </div>
        )}
      </div>
    </div>
  )
}
