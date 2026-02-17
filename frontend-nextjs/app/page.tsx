'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import Header from '@/components/Header'
import TopicSearch from '@/components/TopicSearch'
import MetricCards from '@/components/MetricCards'
import BiasSpectrum from '@/components/BiasSpectrum'
import ArticlesList from '@/components/ArticlesList'
import FilterPanel from '@/components/FilterPanel'
import ReportBias from '@/components/ReportBias'
import { Article, FilterState } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'

export default function Home() {
  const [articles, setArticles] = useState<Article[]>([])
  const [filteredArticles, setFilteredArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(false)
  const [currentTopic, setCurrentTopic] = useState<string>('')
  const [searchMode, setSearchMode] = useState<'browse' | 'topic'>('browse')
  const [filters, setFilters] = useState<FilterState>({
    sources: [],
    biases: ['Left-Leaning', 'Center-Left', 'Centrist', 'Center-Right', 'Right-Leaning'],
    keyword: '',
    dateFrom: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    dateTo: new Date(),
    sortBy: 'date-desc',
    minConfidence: 0,
  })
  const [mlEnabled, setMlEnabled] = useState(false)
  const [showAiReasoning, setShowAiReasoning] = useState(false)

  const fetchNews = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE}/v1/articles/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success && data.articles) {
        setArticles(data.articles)
        setFilteredArticles(data.articles)
      } else {
        console.error('No articles returned:', data.message)
      }
    } catch (error) {
      console.error('Error fetching news:', error)
      alert('Failed to fetch news. Please check if the backend service is running.')
    } finally {
      setLoading(false)
    }
  }

  const classifyWithAI = async () => {
    setLoading(true)
    try {
      // Classify each article using the backend API
      const classifiedArticles = await Promise.all(
        articles.map(async (article) => {
          try {
            const response = await fetch(`${API_BASE}/v1/classify`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: article.title + ' ' + (article.summary || '') }),
            })
            
            if (response.ok) {
              const result = await response.json()
              return {
                ...article,
                ml_bias: result.bias,
                ml_confidence: result.confidence,
                ml_reasoning: result.reasoning,
              }
            }
            return article
          } catch (err) {
            console.error(`Error classifying article ${article.id}:`, err)
            return article
          }
        })
      )
      
      setArticles(classifiedArticles)
      setFilteredArticles(classifiedArticles)
      setMlEnabled(true)
    } catch (error) {
      console.error('Error classifying:', error)
      alert('Failed to classify articles. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const searchByTopic = async (topic: string) => {
    setLoading(true)
    setSearchMode('topic')
    setCurrentTopic(topic)
    try {
      const response = await fetch(
        `${API_BASE}/v1/search?topic=${encodeURIComponent(topic)}&max_articles=30`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      )
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success && data.articles) {
        // Map search results to Article type
        const searchArticles = data.articles.map((article: any) => ({
          ...article,
          ml_bias: article.ml_bias,
          ml_confidence: article.ml_confidence,
          ml_explanation: article.ml_explanation,
        }))
        
        setArticles(searchArticles)
        setFilteredArticles(searchArticles)
        setMlEnabled(true) // ML is automatically applied in topic search
      } else {
        alert(`No articles found for topic: ${topic}`)
      }
    } catch (error) {
      console.error('Error searching topic:', error)
      alert('Failed to search topic. Please check if the backend service is running.')
    } finally {
      setLoading(false)
    }
  }

  const resetToBrowseMode = () => {
    setSearchMode('browse')
    setCurrentTopic('')
    setArticles([])
    setFilteredArticles([])
    setMlEnabled(false)
  }

  useEffect(() => {
    // Apply filters
    let filtered = [...articles]

    // Filter by sources
    if (filters.sources.length > 0) {
      filtered = filtered.filter(a => filters.sources.includes(a.source_name))
    }

    // Filter by bias - use ml_bias from search results if political_bias doesn't exist
    filtered = filtered.filter(a => {
      const bias = a.political_bias || a.ml_bias
      return filters.biases.includes(bias)
    })

    // Filter by keyword
    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase()
      filtered = filtered.filter(a => 
        a.title.toLowerCase().includes(kw) ||
        (a.summary && a.summary.toLowerCase().includes(kw))
      )
    }

    // Filter by date
    filtered = filtered.filter(a => {
      const date = new Date(a.published)
      return date >= filters.dateFrom && date <= filters.dateTo
    })

    // Filter by confidence
    if (mlEnabled && filters.minConfidence > 0) {
      filtered = filtered.filter(a => 
        a.ml_confidence && (a.ml_confidence * 100) >= filters.minConfidence
      )
    }

    // Sort
    switch (filters.sortBy) {
      case 'date-desc':
        filtered.sort((a, b) => new Date(b.published).getTime() - new Date(a.published).getTime())
        break
      case 'date-asc':
        filtered.sort((a, b) => new Date(a.published).getTime() - new Date(b.published).getTime())
        break
      case 'source':
        filtered.sort((a, b) => a.source_name.localeCompare(b.source_name))
        break
      case 'confidence':
        if (mlEnabled) {
          filtered.sort((a, b) => (b.ml_confidence || 0) - (a.ml_confidence || 0))
        }
        break
    }

    setFilteredArticles(filtered)
  }, [filters, articles, mlEnabled])

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-white">
        <Header />

        {/* Topic Search */}
        <TopicSearch onSearch={searchByTopic} loading={loading} />

        {/* Report Bias - Crowdsourcing */}
        <ReportBias />

        {/* Mode Indicator */}
        {searchMode === 'topic' && currentTopic && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-[#142c4c] text-white flex items-center justify-between"
          >
            <div>
              <p className="text-sm font-semibold">Topic Search Results</p>
              <p className="text-lg">"{currentTopic}"</p>
              <p className="text-xs mt-1 opacity-90">
                Showing {filteredArticles.length} articles with AI bias analysis
              </p>
            </div>
            <button
              onClick={resetToBrowseMode}
              className="px-4 py-2 bg-white text-[#142c4c] font-semibold hover:bg-opacity-90 transition-all"
            >
              Clear & Browse All
            </button>
          </motion.div>
        )}

        {/* Action Buttons */}
        {searchMode === 'browse' && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
          >
            <button
              onClick={fetchNews}
              disabled={loading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Fetch Latest News'}
            </button>
            
            <button
              onClick={classifyWithAI}
              disabled={loading || articles.length === 0}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Classifying...' : 'Classify with AI'}
            </button>

            <div className="flex items-center gap-3">
              {mlEnabled && (
                <>
                  <label className="flex items-center gap-2 text-sm font-medium">
                    <input
                      type="checkbox"
                      checked={showAiReasoning}
                      onChange={(e) => setShowAiReasoning(e.target.checked)}
                      className="w-4 h-4"
                    />
                    Show AI Reasoning
                  </label>
                </>
              )}
            </div>
          </motion.div>
        )}

        {articles.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-20"
          >
            <h2 className="text-3xl font-bold mb-2 font-[var(--font-sora)]">
              {searchMode === 'topic' ? 'Searching...' : 'No articles yet'}
            </h2>
            <p className="text-[var(--muted)] text-lg">
              {searchMode === 'topic' 
                ? 'AI is analyzing your topic and searching across all news sources...'
                : 'Search for a topic above, or click Fetch Latest News to browse all sources.'
              }
            </p>
          </motion.div>
        ) : (
          <>
            <MetricCards 
              articles={articles} 
              filteredArticles={filteredArticles}
              mlEnabled={mlEnabled}
            />

            <FilterPanel 
              articles={articles}
              filters={filters}
              setFilters={setFilters}
              mlEnabled={mlEnabled}
            />

            <BiasSpectrum articles={filteredArticles} />

            <ArticlesList 
              articles={filteredArticles}
              mlEnabled={mlEnabled}
              showAiReasoning={showAiReasoning}
            />
          </>
        )}
      </div>
    </main>
  )
}
