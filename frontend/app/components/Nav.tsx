'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useLanguage } from '@/lib/LanguageContext'
import GermanFlag from '@/components/GermanFlag'
import KlarLogo from '@/components/KlarLogo'
import LanguageToggle from './LanguageToggle'

export default function Nav() {
  const pathname = usePathname()
  const isHome = pathname === '/'
  const { t } = useLanguage()
  const l = t.landing

  return (
    <nav
      style={{
        background: 'rgba(10,14,26,0.8)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <KlarLogo size="md" />
          <GermanFlag size={20} />
        </Link>

        <div className="flex items-center gap-6">
          {isHome && (
            <>
              <a
                href="#how-it-works"
                style={{ color: '#9CA3AF', fontSize: '0.875rem', transition: 'color 0.15s' }}
                onMouseEnter={(e) => { e.currentTarget.style.color = '#F9FAFB' }}
                onMouseLeave={(e) => { e.currentTarget.style.color = '#9CA3AF' }}
              >
                {l.navHowItWorks}
              </a>
              <a
                href="#pricing"
                style={{ color: '#9CA3AF', fontSize: '0.875rem', transition: 'color 0.15s' }}
                onMouseEnter={(e) => { e.currentTarget.style.color = '#F9FAFB' }}
                onMouseLeave={(e) => { e.currentTarget.style.color = '#9CA3AF' }}
              >
                {l.navPricing}
              </a>
            </>
          )}
          <LanguageToggle />
        </div>
      </div>
    </nav>
  )
}
