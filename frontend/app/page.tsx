'use client'
import Link from 'next/link'
import { useLanguage } from '@/lib/LanguageContext'

export default function HomePage() {
  const { t } = useLanguage()
  const l = t.landing

  const stats = [
    { num: l.stat1Num, label: l.stat1Label },
    { num: l.stat2Num, label: l.stat2Label },
    { num: l.stat3Num, label: l.stat3Label },
  ]

  const features = [
    { num: '01', title: l.feature1Title, desc: l.feature1Desc },
    { num: '02', title: l.feature2Title, desc: l.feature2Desc },
    { num: '03', title: l.feature3Title, desc: l.feature3Desc },
  ]

  return (
    <div className="flex flex-col min-h-screen" style={{ background: '#0A0E1A' }}>
      {/* Hero */}
      <section
        className="relative flex flex-col items-center justify-center text-center px-6 overflow-hidden"
        style={{ minHeight: '100vh' }}
      >
        <div style={{ position: 'relative', zIndex: 1 }} className="flex flex-col items-center">
          {/* Pill badge */}
          <div
            className="inline-flex items-center rounded-full text-sm px-4 mb-8"
            style={{
              background: 'var(--accent-dim)',
              border: '1px solid rgba(13,148,136,0.3)',
              color: 'var(--accent-light)',
              paddingTop: '6px',
              paddingBottom: '6px',
            }}
          >
            ✦ {l.badge}
          </div>

          {/* Headline */}
          <h1
            className="font-bold"
            style={{
              fontSize: 'clamp(3rem, 8vw, 6rem)',
              letterSpacing: '-0.04em',
              lineHeight: 0.95,
              color: '#F9FAFB',
              maxWidth: '700px',
            }}
          >
            {l.headline1}
            <br />
            {l.headline2}
            <br />
            <span style={{ color: '#F9FAFB', letterSpacing: '-0.06em' }}>{l.headline3}</span>
          </h1>

          {/* Subheadline */}
          <p
            className="mt-6"
            style={{
              color: '#9CA3AF',
              fontSize: '1.125rem',
              maxWidth: '480px',
              lineHeight: 1.6,
            }}
          >
            {l.subheadline}
          </p>

          {/* CTA */}
          <Link
            href="/diagnostic"
            className="cta-button inline-block mt-10 font-semibold"
            style={{
              background: 'var(--accent)',
              color: 'white',
              padding: '16px 32px',
              borderRadius: '9999px',
              fontSize: '1.125rem',
              letterSpacing: '-0.01em',
            }}
          >
            {l.cta}
          </Link>

          <Link
            href="/results/demo"
            className="block text-sm hover:text-white underline"
            style={{ color: '#9CA3AF', marginTop: '12px' }}
          >
            {l.demoLink}
          </Link>

          <p className="mt-4 text-sm" style={{ color: '#6B7280' }}>
            {l.ctaSub}
          </p>
        </div>
      </section>

      {/* Stats bar */}
      <div style={{ borderTop: '1px solid #1F2937', borderBottom: '1px solid #1F2937' }}>
        <div
          className="max-w-3xl mx-auto px-6 flex items-center justify-center gap-16 flex-wrap"
          style={{ paddingTop: '32px', paddingBottom: '32px' }}
        >
          {stats.map(({ num, label }) => (
            <div key={label} className="text-center">
              <div className="font-bold" style={{ fontSize: '1.875rem', color: '#F9FAFB' }}>
                {num}
              </div>
              <div className="text-sm mt-1" style={{ color: '#9CA3AF' }}>
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Features section */}
      <section style={{ padding: '80px 24px', maxWidth: '900px', margin: '0 auto', width: '100%' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: '#F9FAFB', marginBottom: '48px' }}>
          {l.featuresTitle}
        </h2>
        {features.map(({ num, title, desc }, i) => (
          <div key={num} style={{
            display: 'flex',
            gap: '32px',
            padding: '32px 0',
            borderTop: i === 0 ? 'none' : '1px solid rgba(255,255,255,0.08)',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
          }}>
            <span style={{
              fontSize: '4rem',
              fontWeight: 600,
              color: 'var(--accent)',
              lineHeight: 1,
              flexShrink: 0,
              minWidth: '90px',
            }}>{num}</span>
            <div style={{ paddingTop: '8px', flex: 1, minWidth: '200px' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#F9FAFB', marginBottom: '8px' }}>
                {title}
              </h3>
              <p style={{ fontSize: '1rem', color: 'var(--text2)', lineHeight: 1.6, maxWidth: '500px' }}>
                {desc}
              </p>
            </div>
          </div>
        ))}
      </section>

      {/* Footer */}
      <footer
        className="text-center text-sm"
        style={{
          borderTop: '1px solid #1F2937',
          paddingTop: '32px',
          paddingBottom: '32px',
          color: '#6B7280',
        }}
      >
        Klar © 2026 · Powered by Claude AI · Reviewed by humans
      </footer>
    </div>
  )
}
