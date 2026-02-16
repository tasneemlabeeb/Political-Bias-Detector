'use client'

import { motion } from 'framer-motion'
import { Article, BIAS_COLORS, BIAS_ORDER } from '@/types'

interface Props {
  articles: Article[]
}

export default function BiasSpectrum({ articles }: Props) {
  const biasCounts = articles.reduce((acc, article) => {
    const bias = article.political_bias || article.ml_bias || 'Centrist'
    acc[bias] = (acc[bias] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const total = articles.length || 1

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="mb-8"
    >
      <h2 className="text-xl font-bold font-[var(--font-sora)] mb-4 pb-2 border-b border-[var(--line)]">
        Bias Spectrum
      </h2>

      <div className="card p-6">
        <div className="flex h-8 overflow-hidden shadow-inner border border-gray-200/50 mb-3">
          {BIAS_ORDER.map((bias) => {
            const count = biasCounts[bias] || 0
            const percentage = (count / total) * 100
            
            if (percentage === 0) return null

            return (
              <motion.div
                key={bias}
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className="flex items-center justify-center text-white text-xs font-bold cursor-pointer hover:brightness-110 transition-all"
                style={{ backgroundColor: BIAS_COLORS[bias] }}
                title={`${bias}: ${count} (${percentage.toFixed(0)}%)`}
              >
                {percentage > 8 && count}
              </motion.div>
            )
          })}
        </div>

        <div className="flex flex-wrap justify-center gap-4 mt-4">
          {BIAS_ORDER.map((bias) => (
            <div key={bias} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3"
                style={{ backgroundColor: BIAS_COLORS[bias] }}
              />
              <span className="text-[var(--muted)] font-medium">{bias}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
