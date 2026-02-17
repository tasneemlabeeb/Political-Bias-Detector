'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BIAS_ORDER, BIAS_COLORS, BIAS_DISPLAY_NAMES } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export default function ReportBias() {
  const [isOpen, setIsOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [articleText, setArticleText] = useState('')
  const [biasLabel, setBiasLabel] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const canSubmit = biasLabel && (url.trim() || title.trim())

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) setIsOpen(false)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen])

  const resetForm = () => {
    setUrl('')
    setTitle('')
    setArticleText('')
    setBiasLabel('')
    setResult(null)
  }

  const handleClose = () => {
    setIsOpen(false)
    resetForm()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    setSubmitting(true)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE}/v1/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url.trim() || undefined,
          title: title.trim() || undefined,
          article_text: articleText.trim() || undefined,
          bias_label: biasLabel,
        }),
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setResult({ success: true, message: data.message })
        setUrl('')
        setTitle('')
        setArticleText('')
        setBiasLabel('')
      } else {
        setResult({
          success: false,
          message: data.detail || 'Failed to submit report. Please try again.',
        })
      }
    } catch {
      setResult({
        success: false,
        message: 'Network error. Make sure the backend is running.',
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      {/* Trigger Button */}
      <div className="mb-8">
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-3 px-6 py-3 bg-white border-2 border-[var(--line)] hover:border-[#142c4c] transition-all w-full"
        >
          <svg className="w-5 h-5 text-[#142c4c]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-left">
            <span className="font-semibold text-[#142c4c]">Report Article Bias</span>
            <span className="text-sm text-[var(--muted)] ml-2">Help improve our model with your input</span>
          </div>
        </button>
      </div>

      {/* Modal Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={handleClose}
          >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50" />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="relative bg-white w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="sticky top-0 bg-white border-b border-[var(--line)] p-6 pb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-[#142c4c]">Report Article Bias</h2>
                  <p className="text-sm text-[var(--muted)] mt-1">
                    Help improve our model by labeling article bias
                  </p>
                </div>
                <button
                  onClick={handleClose}
                  className="text-[var(--muted)] hover:text-[var(--ink)] transition-colors p-1"
                  aria-label="Close"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-1 text-[var(--ink)]">
                    Article URL
                  </label>
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/article..."
                    className="w-full px-4 py-3 border-2 border-[var(--line)] focus:border-[#142c4c] focus:outline-none transition-colors"
                    disabled={submitting}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1 text-[var(--ink)]">
                    Article Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter the article headline..."
                    maxLength={512}
                    className="w-full px-4 py-3 border-2 border-[var(--line)] focus:border-[#142c4c] focus:outline-none transition-colors"
                    disabled={submitting}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-1 text-[var(--ink)]">
                    Article Text <span className="font-normal text-[var(--muted)]">(optional)</span>
                  </label>
                  <textarea
                    value={articleText}
                    onChange={(e) => setArticleText(e.target.value)}
                    placeholder="Paste article content here for more accurate future training..."
                    rows={3}
                    className="w-full px-4 py-3 border-2 border-[var(--line)] focus:border-[#142c4c] focus:outline-none transition-colors resize-y"
                    disabled={submitting}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2 text-[var(--ink)]">
                    Perceived Bias
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {BIAS_ORDER.map((bias) => (
                      <button
                        key={bias}
                        type="button"
                        onClick={() => setBiasLabel(bias)}
                        className={`px-4 py-2 text-sm font-semibold border-2 transition-all ${
                          biasLabel === bias
                            ? 'text-white border-transparent'
                            : 'bg-white text-[var(--ink)] border-[var(--line)] hover:border-[#142c4c]'
                        }`}
                        style={biasLabel === bias ? { backgroundColor: BIAS_COLORS[bias] } : {}}
                        disabled={submitting}
                      >
                        {bias}
                      </button>
                    ))}
                  </div>
                </div>

                {!url.trim() && !title.trim() && (
                  <p className="text-xs text-[var(--muted)]">
                    Please provide at least a URL or article title.
                  </p>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={!canSubmit || submitting}
                    className="flex-1 px-8 py-3 bg-[#142c4c] text-white font-semibold hover:bg-opacity-90 disabled:bg-[var(--muted)] disabled:cursor-not-allowed transition-all"
                  >
                    {submitting ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Submitting...
                      </span>
                    ) : (
                      'Submit Report'
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={handleClose}
                    className="px-6 py-3 border-2 border-[var(--line)] text-[var(--muted)] font-semibold hover:border-[#142c4c] hover:text-[var(--ink)] transition-all"
                  >
                    Cancel
                  </button>
                </div>

                <AnimatePresence>
                  {result && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className={`p-4 ${
                        result.success
                          ? 'bg-green-50 border-l-4 border-green-500 text-green-800'
                          : 'bg-red-50 border-l-4 border-red-500 text-red-800'
                      }`}
                    >
                      <p className="text-sm font-medium">{result.message}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
