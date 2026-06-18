'use client'
import Link from 'next/link'
import Image from 'next/image'
import { useState } from 'react'
import { BarChart2, Briefcase, FileText, ShieldCheck, Lock, CheckCircle, ChevronDown } from 'lucide-react'
import { useLanguage } from '@/lib/LanguageContext'

const KLAR_BLUE = '#2563EB'
const BLUE_DIM = 'rgba(37,99,235,0.12)'

export default function HomePage() {
  const { t } = useLanguage()
  const l = t.landing
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  const stats = [
    { num: l.stat1Num, label: l.stat1Label },
    { num: l.stat2Num, label: l.stat2Label },
    { num: l.stat3Num, label: l.stat3Label },
  ]

  const steps = [
    { num: '01', title: l.step1Title, desc: l.step1Desc },
    { num: '02', title: l.step2Title, desc: l.step2Desc },
    { num: '03', title: l.step3Title, desc: l.step3Desc },
  ]

  const cards = [
    {
      icon: <BarChart2 size={24} color={KLAR_BLUE} />,
      title: l.card1Title,
      desc: l.card1Desc,
      badge: l.card1Badge,
      badgeBg: BLUE_DIM,
      badgeColor: '#93C5FD',
    },
    {
      icon: <Briefcase size={24} color={KLAR_BLUE} />,
      title: l.card2Title,
      desc: l.card2Desc,
      badge: l.card2Badge,
      badgeBg: BLUE_DIM,
      badgeColor: '#93C5FD',
    },
    {
      icon: <FileText size={24} color={KLAR_BLUE} />,
      title: l.card3Title,
      desc: l.card3Desc,
      badge: l.card3Badge,
      badgeBg: BLUE_DIM,
      badgeColor: '#93C5FD',
    },
  ]

  const trust = [
    { icon: <ShieldCheck size={20} color='#6B7280' />, title: l.trust1Title, desc: l.trust1Desc },
    { icon: <Lock size={20} color='#6B7280' />, title: l.trust2Title, desc: l.trust2Desc },
    { icon: <CheckCircle size={20} color='#6B7280' />, title: l.trust3Title, desc: l.trust3Desc },
  ]

  const faqs = [
    { q: l.faq1Q, a: l.faq1A },
    { q: l.faq2Q, a: l.faq2A },
    { q: l.faq3Q, a: l.faq3A },
    { q: l.faq4Q, a: l.faq4A },
    { q: l.faq5Q, a: l.faq5A },
  ]

  return (
    <div className="flex flex-col min-h-screen" style={{ background: '#0A0E1A' }}>

      {/* ── HERO ───────────────────────────────────────────────── */}
      <section
        className="relative flex flex-col items-center justify-center text-center px-6 overflow-hidden"
        style={{ minHeight: '100vh' }}
      >
        <div style={{ position: 'relative', zIndex: 1 }} className="flex flex-col items-center">
          {/* Logo mark */}
          <Image
            src="/logo.svg"
            alt="Klar"
            width={64}
            height={64}
            priority
            style={{ marginBottom: '24px' }}
          />

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

      {/* ── STATS BAR ──────────────────────────────────────────── */}
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

      {/* ── SECTION 2: HOW IT WORKS ────────────────────────────── */}
      <section
        id="how-it-works"
        style={{ padding: '96px 24px', maxWidth: '960px', margin: '0 auto', width: '100%' }}
      >
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 700,
            color: '#F9FAFB',
            marginBottom: '64px',
            letterSpacing: '-0.03em',
          }}
        >
          {l.howItWorksTitle}
        </h2>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '0',
            position: 'relative',
          }}
        >
          {/* Connecting line — desktop only via inline style trick */}
          <div
            aria-hidden
            style={{
              position: 'absolute',
              top: '28px',
              left: '60px',
              right: '60px',
              height: '1px',
              background: 'rgba(37,99,235,0.25)',
              pointerEvents: 'none',
            }}
          />

          {steps.map(({ num, title, desc }) => (
            <div
              key={num}
              style={{
                padding: '0 32px 0 0',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: BLUE_DIM,
                  border: `1px solid rgba(37,99,235,0.3)`,
                  marginBottom: '20px',
                  position: 'relative',
                  zIndex: 1,
                }}
              >
                <span
                  style={{
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: KLAR_BLUE,
                    letterSpacing: '-0.02em',
                  }}
                >
                  {num}
                </span>
              </div>
              <h3
                style={{
                  fontSize: '1.125rem',
                  fontWeight: 600,
                  color: '#F9FAFB',
                  marginBottom: '8px',
                  letterSpacing: '-0.02em',
                }}
              >
                {title}
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#9CA3AF', lineHeight: 1.6 }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── SECTION 3: WHAT YOU GET ────────────────────────────── */}
      <section
        id="pricing"
        style={{
          padding: '96px 24px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div style={{ maxWidth: '960px', margin: '0 auto' }}>
          <h2
            style={{
              fontSize: 'clamp(1.5rem, 3vw, 2rem)',
              fontWeight: 700,
              color: '#F9FAFB',
              marginBottom: '48px',
              letterSpacing: '-0.03em',
            }}
          >
            {l.whatYouGetTitle}
          </h2>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '20px',
            }}
          >
            {cards.map(({ icon, title, desc, badge, badgeBg, badgeColor }) => (
              <div
                key={title}
                className="glass"
                style={{
                  borderRadius: '16px',
                  padding: '28px',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                {/* Badge */}
                <span
                  style={{
                    position: 'absolute',
                    top: '20px',
                    right: '20px',
                    background: badgeBg,
                    color: badgeColor,
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '4px 10px',
                    borderRadius: '9999px',
                    border: `1px solid rgba(37,99,235,0.25)`,
                    letterSpacing: '0.02em',
                  }}
                >
                  {badge}
                </span>

                {/* Icon */}
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '10px',
                    background: BLUE_DIM,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {icon}
                </div>

                <h3
                  style={{
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                    color: '#F9FAFB',
                    letterSpacing: '-0.02em',
                    marginTop: '4px',
                    paddingRight: '40px',
                  }}
                >
                  {title}
                </h3>
                <p style={{ fontSize: '0.875rem', color: '#9CA3AF', lineHeight: 1.65 }}>
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 4: TRUST ───────────────────────────────────── */}
      <section
        style={{
          padding: '80px 24px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div style={{ maxWidth: '960px', margin: '0 auto' }}>
          <h2
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              color: '#6B7280',
              marginBottom: '40px',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
            }}
          >
            {l.trustTitle}
          </h2>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '32px',
            }}
          >
            {trust.map(({ icon, title, desc }) => (
              <div key={title} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {icon}
                  <span
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      color: '#9CA3AF',
                    }}
                  >
                    {title}
                  </span>
                </div>
                <p style={{ fontSize: '0.8125rem', color: '#6B7280', lineHeight: 1.6, paddingLeft: '28px' }}>
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 5: FAQ ─────────────────────────────────────── */}
      <section
        style={{
          padding: '80px 24px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div style={{ maxWidth: '680px', margin: '0 auto' }}>
          <h2
            style={{
              fontSize: 'clamp(1.5rem, 3vw, 2rem)',
              fontWeight: 700,
              color: '#F9FAFB',
              marginBottom: '40px',
              letterSpacing: '-0.03em',
            }}
          >
            {l.faqTitle}
          </h2>

          <div>
            {faqs.map(({ q, a }, i) => (
              <div
                key={i}
                style={{
                  borderTop: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '20px 0',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                    gap: '16px',
                    fontFamily: 'inherit',
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.9375rem',
                      fontWeight: 600,
                      color: '#F9FAFB',
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {q}
                  </span>
                  <ChevronDown
                    size={18}
                    color='#6B7280'
                    style={{
                      flexShrink: 0,
                      transition: 'transform 0.2s ease',
                      transform: openFaq === i ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}
                  />
                </button>

                <div
                  style={{
                    overflow: 'hidden',
                    maxHeight: openFaq === i ? '300px' : '0',
                    transition: 'max-height 0.3s ease',
                  }}
                >
                  <p
                    style={{
                      fontSize: '0.9375rem',
                      color: '#9CA3AF',
                      lineHeight: 1.7,
                      paddingBottom: '20px',
                    }}
                  >
                    {a}
                  </p>
                </div>
              </div>
            ))}
            {/* Bottom border */}
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }} />
          </div>
        </div>
      </section>

      {/* ── SECTION 6: FINAL CTA ───────────────────────────────── */}
      <section
        style={{
          background: 'linear-gradient(135deg, #0f1c3f 0%, #0A0E1A 60%, #0d1a3a 100%)',
          borderTop: '1px solid rgba(37,99,235,0.2)',
          padding: '96px 24px',
          textAlign: 'center',
        }}
      >
        <div style={{ maxWidth: '560px', margin: '0 auto' }}>
          <h2
            style={{
              fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
              fontWeight: 700,
              color: '#F9FAFB',
              letterSpacing: '-0.04em',
              marginBottom: '16px',
            }}
          >
            {l.finalCtaTitle}
          </h2>
          <p
            style={{
              color: '#9CA3AF',
              fontSize: '1rem',
              marginBottom: '36px',
              lineHeight: 1.6,
            }}
          >
            {l.finalCtaSub}
          </p>
          <Link
            href="/diagnostic"
            className="inline-block font-semibold"
            style={{
              background: KLAR_BLUE,
              color: 'white',
              padding: '16px 36px',
              borderRadius: '9999px',
              fontSize: '1.0625rem',
              letterSpacing: '-0.01em',
              transition: 'transform 0.2s ease, background 0.2s ease',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLAnchorElement).style.transform = 'scale(1.02)'
              ;(e.currentTarget as HTMLAnchorElement).style.background = '#1D4ED8'
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLAnchorElement).style.transform = 'scale(1)'
              ;(e.currentTarget as HTMLAnchorElement).style.background = KLAR_BLUE
            }}
          >
            {l.finalCtaBtn}
          </Link>
        </div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────────── */}
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
