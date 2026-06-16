'use client'

import { useState } from 'react'
import { useLanguage } from '@/lib/LanguageContext'

export function ShareButton({ id }: { id: string }) {
  const [copied, setCopied] = useState(false)
  const { t } = useLanguage()

  async function handleShare() {
    const url = `${window.location.origin}/results/${id}`
    if (navigator.share) {
      await navigator.share({ title: 'My Klar Germany Score', url })
    } else {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      onClick={handleShare}
      className="glass rounded-full font-medium transition-all"
      style={{ padding: '12px 24px', color: '#F9FAFB' }}
    >
      {copied ? `${t.results.copied} ✓` : t.results.shareBtn}
    </button>
  )
}
