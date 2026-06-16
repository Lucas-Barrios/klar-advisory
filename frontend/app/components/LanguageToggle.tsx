'use client'
import { useLanguage } from '@/lib/LanguageContext'

export default function LanguageToggle() {
  const { lang, setLang } = useLanguage()
  return (
    <button
      onClick={() => setLang(lang === 'en' ? 'es' : 'en')}
      className="rounded-full text-xs px-3 py-1"
      style={{
        background: 'rgba(255,255,255,0.08)',
        border: '1px solid rgba(255,255,255,0.12)',
        color: '#9CA3AF',
        cursor: 'pointer',
        fontFamily: 'inherit',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'rgba(255,255,255,0.14)'
        e.currentTarget.style.color = '#F9FAFB'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'rgba(255,255,255,0.08)'
        e.currentTarget.style.color = '#9CA3AF'
      }}
    >
      {lang === 'en' ? '🇬🇧 EN' : '🇪🇸 ES'}
    </button>
  )
}
