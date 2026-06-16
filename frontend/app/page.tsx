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
        {/* Background blob */}
        <div
          aria-hidden
          style={{
            position: 'absolute',
            top: '20%',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '600px',
            height: '600px',
            background: 'radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />

        <div style={{ position: 'relative', zIndex: 1 }} className="flex flex-col items-center">
          {/* Pill badge */}
          <div
            className="inline-flex items-center rounded-full text-sm px-4 mb-8"
            style={{
              background: 'rgba(59,130,246,0.1)',
              border: '1px solid rgba(59,130,246,0.3)',
              color: '#60A5FA',
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
            <span className="gradient-text">{l.headline3}</span>
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
              background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
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
              <div className="gradient-text font-bold" style={{ fontSize: '1.875rem' }}>
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
      <section className="max-w-5xl mx-auto px-6 w-full" style={{ paddingTop: '96px', paddingBottom: '96px' }}>
        <h2
          className="text-center font-bold mb-12"
          style={{ fontSize: '2.25rem', letterSpacing: '-0.03em', color: '#F9FAFB' }}
        >
          {l.featuresTitle}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {features.map(({ num, title, desc }) => (
            <div
              key={num}
              className="feature-card glass rounded-2xl cursor-default"
              style={{ padding: '32px' }}
            >
              <div className="gradient-text font-bold" style={{ fontSize: '3rem', letterSpacing: '-0.03em' }}>
                {num}
              </div>
              <h3
                className="font-semibold mt-4 mb-3"
                style={{ fontSize: '1.125rem', color: '#F9FAFB' }}
              >
                {title}
              </h3>
              <p style={{ color: '#9CA3AF', fontSize: '0.9375rem', lineHeight: 1.6 }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
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
