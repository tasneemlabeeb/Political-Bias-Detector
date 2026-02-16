'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { MessageCircle, Search, TrendingUp, Hash } from 'lucide-react'

export default function SocialMediaPage() {
  const [platform, setPlatform] = useState<'reddit' | 'twitter'>('reddit')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)

  const analyzeReddit = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/social-media/reddit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subreddit: query,
          limit: 50,
          time_filter: 'day',
          analyze_comments: true
        })
      })
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error analyzing Reddit:', error)
    }
    setLoading(false)
  }

  const analyzeTwitter = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/social-media/twitter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          max_results: 100
        })
      })
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error analyzing Twitter:', error)
    }
    setLoading(false)
  }

  const handleAnalyze = () => {
    if (!query.trim()) return
    platform === 'reddit' ? analyzeReddit() : analyzeTwitter()
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
            Social Media Bias Analysis
          </h1>
          <p className="text-[var(--muted)]">
            Analyze political bias in Twitter and Reddit conversations
          </p>
        </motion.div>

        {/* Platform Selection */}
        <div className="card p-6 mb-8">
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setPlatform('reddit')}
              className={`flex-1 py-3 px-6 font-bold transition-all ${
                platform === 'reddit'
                  ? 'bg-[#142c4c] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <MessageCircle className="w-5 h-5 inline-block mr-2" />
              Reddit
            </button>
            <button
              onClick={() => setPlatform('twitter')}
              className={`flex-1 py-3 px-6 font-bold transition-all ${
                platform === 'twitter'
                  ? 'bg-[#142c4c] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Hash className="w-5 h-5 inline-block mr-2" />
              Twitter
            </button>
          </div>

          <div className="flex gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                platform === 'reddit'
                  ? 'Enter subreddit name (e.g., politics)'
                  : 'Enter search query or hashtag'
              }
              className="flex-1 border border-gray-300 p-3 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !query.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Search className="w-5 h-5 inline-block mr-2" />
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </div>

        {/* Results */}
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {results.posts_count || results.posts?.length || 0}
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Posts Analyzed
                </div>
              </div>
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {results.comments_count || 0}
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Comments Analyzed
                </div>
              </div>
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {(results.avg_confidence * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Avg Confidence
                </div>
              </div>
              <div className="card p-6 text-center">
                <div className="text-3xl font-bold text-[var(--ink)] mb-2">
                  {Object.keys(results.post_bias_distribution || results.bias_distribution || {}).length}
                </div>
                <div className="text-sm text-[var(--muted)] font-semibold">
                  Bias Categories
                </div>
              </div>
            </div>

            {/* Bias Distribution */}
            <div className="card p-6">
              <h3 className="text-xl font-bold text-[var(--ink)] mb-4">
                Bias Distribution
              </h3>
              <div className="space-y-3">
                {Object.entries(results.post_bias_distribution || results.bias_distribution || {}).map(
                  ([bias, count]: [string, any]) => (
                    <div key={bias} className="flex items-center gap-4">
                      <div className="w-32 font-semibold text-sm">{bias}</div>
                      <div className="flex-1 h-8 bg-gray-200 relative overflow-hidden">
                        <div
                          className="h-full bg-[#142c4c] flex items-center px-3 text-white text-sm font-bold"
                          style={{
                            width: `${(count / (results.posts_count || 1)) * 100}%`
                          }}
                        >
                          {count}
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>

            {/* Posts */}
            <div className="card p-6">
              <h3 className="text-xl font-bold text-[var(--ink)] mb-4">
                Recent Posts
              </h3>
              <div className="space-y-4">
                {(results.posts || []).slice(0, 10).map((post: any) => (
                  <div
                    key={post.post_id}
                    className="border border-gray-200 p-4 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">u/{post.author}</span>
                        {post.political_bias && (
                          <span className="px-2 py-1 bg-[#142c4c] text-white text-xs font-bold">
                            {post.political_bias}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-[var(--muted)]">
                        {new Date(post.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--ink)] mb-2 line-clamp-3">
                      {post.content}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-[var(--muted)]">
                      <span>↑ {post.score}</span>
                      <span>💬 {post.comments_count}</span>
                      {post.ml_confidence && (
                        <span>Confidence: {(post.ml_confidence * 100).toFixed(0)}%</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {!results && !loading && (
          <div className="card p-12 text-center">
            <TrendingUp className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-bold text-[var(--ink)] mb-2">
              Analyze Social Media Conversations
            </h3>
            <p className="text-[var(--muted)]">
              Select a platform and enter a query to analyze political bias in social media posts
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
