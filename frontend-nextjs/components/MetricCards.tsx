'use client'

import { motion } from 'framer-motion'
import { Article } from '@/types'
import { Newspaper, Search, Globe, Target } from 'lucide-react'

interface Props {
  articles: Article[]
  filteredArticles: Article[]
  mlEnabled: boolean
}

export default function MetricCards({ articles, filteredArticles, mlEnabled }: Props) {
  const avgConfidence = mlEnabled
    ? (articles.reduce((sum, a) => sum + (a.ml_confidence || 0), 0) / articles.length * 100).toFixed(0)
    : null

  const metrics = [
    {
      icon: Newspaper,
      label: 'Total Articles',
      value: articles.length,
      delay: 0,
    },
    {
      icon: Search,
      label: 'Showing',
      value: filteredArticles.length,
      delay: 0.06,
    },
    {
      icon: Globe,
      label: 'Sources',
      value: new Set(articles.map(a => a.source_name)).size,
      delay: 0.12,
    },
    {
      icon: Target,
      label: avgConfidence ? 'Avg AI Confidence' : 'Bias Categories',
      value: avgConfidence ? `${avgConfidence}%` : new Set(articles.map(a => a.political_bias)).size,
      delay: 0.18,
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {metrics.map((metric, idx) => {
        const Icon = metric.icon
        return (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: metric.delay, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="card p-6 text-center group relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 right-0 h-1 bg-[#142c4c] transform scale-x-0 transition-transform duration-300 group-hover:scale-x-100" />
            
            <Icon className="w-8 h-8 mx-auto mb-3 text-[#142c4c]" strokeWidth={2} />
            
            <div className="text-4xl font-extrabold font-[var(--font-sora)] mb-2 text-[var(--ink)]">
              {metric.value}
            </div>
            
            <div className="text-xs font-bold tracking-wider uppercase text-[var(--muted)]">
              {metric.label}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
