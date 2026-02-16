'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Newspaper, MessageCircle, Video, Network } from 'lucide-react'

export default function Navigation() {
  const pathname = usePathname()
  
  const links = [
    { href: '/', label: 'News Reader', icon: Newspaper },
    { href: '/social-media', label: 'Social Media', icon: MessageCircle },
    { href: '/media', label: 'Video & Audio', icon: Video },
    { href: '/citations', label: 'Citation Network', icon: Network },
  ]
  
  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#142c4c] flex items-center justify-center">
              <span className="text-white font-bold text-sm">PB</span>
            </div>
            <span className="font-bold text-lg text-[var(--ink)]">
              Bias Detector
            </span>
          </div>
          
          <div className="flex gap-1">
            {links.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all ${
                    isActive
                      ? 'text-[#142c4c] border-b-2 border-[#142c4c]'
                      : 'text-[var(--muted)] hover:text-[var(--ink)]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
