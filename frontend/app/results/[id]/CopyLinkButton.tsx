'use client'
import { useState } from 'react'
import { useLanguage } from '@/lib/LanguageContext'

export default function CopyLinkButton({ id }: { id: string }) {
  const [copied, setCopied] = useState(false)
  const { t } = useLanguage()

  const handleCopy = async () => {
    const url = window.location.href
    await navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      style={{
        marginTop: '16px',
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '9999px',
        padding: '8px 20px',
        fontSize: '13px',
        color: copied ? '#0D9488' : '#9CA3AF',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      {copied ? `✓ ${t.results.copied}` : `🔗 ${t.results.copyLink}`}
    </button>
  )
}
