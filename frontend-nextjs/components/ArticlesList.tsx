'use client'

import { motion } from 'framer-motion'
import { Article, BIAS_COLORS, BIAS_DISPLAY_NAMES } from '@/types'
import { format } from 'date-fns'
import { ExternalLink } from 'lucide-react'

interface Props {
  articles: Article[]
  mlEnabled: boolean
  showAiReasoning: boolean
}

export default function ArticlesList({ articles, mlEnabled, showAiReasoning }: Props) {
  if (articles.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-[var(--muted)]">No articles match your current filters.</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-xl font-bold font-[var(--font-sora)] mb-4 pb-2 border-b border-[var(--line)]">
        Articles ({articles.length})
      </h2>

      <div className="space-y-4">
        {articles.map((article, idx) => {
          const biasLabel = article.political_bias || article.ml_bias || 'Centrist'
          const biasColor = BIAS_COLORS[biasLabel]

          return (
            <motion.div
              key={article.id || idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.03, 0.45) }}
              className="card p-6 border-l-4 relative hover:shadow-xl"
              style={{ borderLeftColor: biasColor }}
            >
              <a
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="group"
              >
                <h3 className="text-xl font-semibold font-[var(--font-sora)] mb-3 group-hover:text-accent transition-colors flex items-start gap-2">
                  <span className="flex-1">{article.title}</span>
                  <ExternalLink className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                </h3>
              </a>

              <div className="flex flex-wrap gap-2 mb-3">
                <span
                  className="px-3 py-1 text-white text-xs font-bold"
                  style={{ backgroundColor: biasColor }}
                >
                  {BIAS_DISPLAY_NAMES[biasLabel] || biasLabel}
                </span>

                {mlEnabled && article.ml_bias && (
                  <span
                    className="px-3 py-1 text-white text-xs font-bold"
                    style={{ backgroundColor: BIAS_COLORS[article.ml_bias] }}
                  >
                    AI: {BIAS_DISPLAY_NAMES[article.ml_bias] || article.ml_bias}
                  </span>
                )}

                <span className="px-3 py-1 bg-amber-100 text-amber-800 text-xs font-medium border border-amber-200">
                  {article.source_name}
                </span>

                <span className="px-3 py-1 text-xs text-[var(--muted)]">
                  {format(new Date(article.published), 'MMM dd, yyyy')}
                </span>
              </div>

              {mlEnabled && article.ml_confidence && (
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                    AI Confidence
                  </span>
                  <div className="flex-1 h-2 bg-gray-200 overflow-hidden shadow-inner">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${article.ml_confidence * 100}%` }}
                      transition={{ duration: 0.8, ease: 'easeOut' }}
                      className="h-full relative overflow-hidden"
                      style={{
                        backgroundColor:
                          article.ml_confidence >= 0.7
                            ? '#43a047'
                            : article.ml_confidence >= 0.5
                            ? '#ffa726'
                            : '#e53935',
                      }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                    </motion.div>
                  </div>
                  <span
                    className="text-xs font-bold min-w-[3rem] text-right"
                    style={{
                      color:
                        article.ml_confidence >= 0.7
                          ? '#43a047'
                          : article.ml_confidence >= 0.5
                          ? '#ffa726'
                          : '#e53935',
                    }}
                  >
                    {(article.ml_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}

              {article.summary && (
                <p className="text-[var(--muted)] leading-relaxed mb-3">
                  {article.summary.length > 300
                    ? `${article.summary.substring(0, 300)}...`
                    : article.summary}
                </p>
              )}

              {mlEnabled && showAiReasoning && article.ml_explanation && (
                <div className="mt-3 p-3 bg-teal-50 border border-teal-200 text-sm text-teal-900">
                  <div className="flex items-start gap-2">
                    <span className="font-semibold text-xs uppercase tracking-wider">AI Analysis:</span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed">{article.ml_explanation}</p>
                  {article.ml_direction_score !== undefined && (
                    <div className="mt-2 text-xs space-y-0.5">
                      <div>Direction score: {article.ml_direction_score.toFixed(2)}</div>
                      <div>Bias intensity: {((article.bias_intensity || 0) * 100).toFixed(0)}%</div>
                      <div>
                        Lexical L/R hits: {article.ml_lexical_left_hits}/{article.ml_lexical_right_hits}
                      </div>
                      <div>Loaded terms: {article.ml_loaded_language_hits}</div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
