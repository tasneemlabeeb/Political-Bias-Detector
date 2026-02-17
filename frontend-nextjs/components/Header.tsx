'use client'

import { motion } from 'framer-motion'

export default function Header() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 pb-6 border-b-2 border-[var(--line)] relative text-center"
    >
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-32 bg-[#142c4c]" />
      
      <p className="text-xs font-bold tracking-widest uppercase text-[#142c4c] mb-2">
        Cross-Source Intelligence
      </p>
      
      <h1 className="text-4xl md:text-5xl font-extrabold font-[var(--font-sora)] tracking-tight mb-3">
        Political Bias Detector
      </h1>
      
      <p className="text-[var(--muted)] text-lg max-w-4xl leading-relaxed mx-auto">
        Track narrative framing across outlets with ML ensemble predictions, lexical signals, 
        and confidence diagnostics in one streamlined interface.
      </p>
    </motion.div>
  )
}
