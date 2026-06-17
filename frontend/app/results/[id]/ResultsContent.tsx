'use client'

import { useLanguage } from '@/lib/LanguageContext'
import CopyLinkButton from './CopyLinkButton'
import { ShareButton } from './ShareButton'
import DownloadPdfButton from './DownloadPdfButton'
import DocumentFactoryClient from './DocumentFactoryClient'
import { Dumbbell, TrendingUp, Star, Rocket, ClipboardList, Target } from 'lucide-react'

type RoadmapStep = {
  month: number
  title: string
  description: string
  action_items: string[]
}

type Recommendation = {
  name: string
  type: string
  description: string
  url: string | null
}

type DimensionScores = {
  language: number
  education: number
  pathway_fit: number
  timeline: number
  financial: number
  documentation: number
}

export type Diagnostic = {
  id: string
  status: 'pending' | 'approved' | 'rejected'
  overall_score: number | null
  summary: string | null
  next_step_message?: string | null
  dimension_scores: DimensionScores | null
  roadmap: RoadmapStep[] | null
  recommendations: Recommendation[] | null
  completed_steps: number[] | null
  matches_unlocked?: boolean
  documents_unlocked?: boolean
  student?: {
    name?: string | null
  } | null
  students: {
    name?: string | null
    full_name?: string | null
    email?: string | null
    pathway?: string | null
  } | null
}

function studentDisplayName(diagnostic: Diagnostic): string {
  return (
    diagnostic.students?.name
    ?? diagnostic.students?.full_name
    ?? diagnostic.student?.name
    ?? 'Student'
  )
}

function scoreColor(score: number): string {
  if (score < 40) return '#EF4444'
  if (score < 60) return '#F59E0B'
  if (score < 80) return '#3B82F6'
  return '#0D9488'
}

function ScoreTierIcon({ score }: { score: number }) {
  const color = scoreColor(score)
  if (score < 40) return <Dumbbell size={28} color={color} />
  if (score < 60) return <TrendingUp size={28} color={color} />
  if (score < 80) return <Star size={28} color={color} />
  return <Rocket size={28} color={color} />
}

function scoreLabel(score: number): { label: string; sub: string } {
  if (score < 40) return { label: 'Not ready yet', sub: "But don't worry — your roadmap starts here." }
  if (score < 60) return { label: 'Getting there', sub: "You're closer than you think." }
  if (score < 80) return { label: 'Ready with preparation', sub: 'You have a strong foundation.' }
  return { label: 'Strong candidate', sub: 'Germany is within reach.' }
}

const DIMENSIONS: { key: keyof DimensionScores; label: string }[] = [
  { key: 'language', label: 'German Language' },
  { key: 'education', label: 'Education' },
  { key: 'pathway_fit', label: 'Pathway Fit' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'financial', label: 'Finances' },
  { key: 'documentation', label: 'Documentation' },
]

export default function ResultsContent({
  diagnostic,
  id,
  notFound,
}: {
  diagnostic: Diagnostic | null
  id: string
  notFound: boolean
}) {
  const { t } = useLanguage()
  const r = t.results

  if (notFound || !diagnostic) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#0A0E1A',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        textAlign: 'center',
        padding: '24px'
      }}>
        <div style={{ marginBottom: '16px' }}>
          <Rocket size={48} color="#6B7280" />
        </div>
        <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#F9FAFB', margin: 0 }}>
          Diagnostic not found
        </h2>
        <p style={{
          color: '#9CA3AF',
          marginTop: '12px',
          marginBottom: '8px',
          maxWidth: '360px',
          lineHeight: 1.6
        }}>
          This diagnostic ID does not exist or has not been submitted yet.
        </p>
        <p style={{ color: '#6B7280', fontSize: '12px', marginBottom: '32px', fontFamily: 'monospace' }}>
          ID: {id}
        </p>
        <a href="/diagnostic" style={{
          background: 'var(--accent)',
          color: 'white',
          padding: '12px 28px',
          borderRadius: '9999px',
          fontWeight: 600,
          textDecoration: 'none',
          fontSize: '15px'
        }}>
          Start a new diagnostic →
        </a>
      </div>
    )
  }

  if (diagnostic.status === 'pending') {
    return (
      <div
        className="min-h-screen flex items-center justify-center px-4"
        style={{ background: '#0A0E1A' }}
      >
        <div className="text-center" style={{ maxWidth: '420px' }}>
          <div
            className="mx-auto mb-6 flex items-center justify-center"
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '9999px',
              background: 'var(--accent-dim)',
              border: '1px solid rgba(13,148,136,0.3)',
            }}
          >
            <span style={{ color: 'var(--accent)', fontSize: '1.875rem' }}>✓</span>
          </div>

          <h1
            className="font-bold"
            style={{
              fontSize: '1.875rem',
              color: '#F9FAFB',
              letterSpacing: '-0.02em',
              marginTop: '24px',
            }}
          >
            {r.pendingTitle}
          </h1>

          <p
            className="mt-4 leading-relaxed"
            style={{ color: '#9CA3AF', fontSize: '0.9375rem', maxWidth: '420px' }}
          >
            {r.pendingBody}{' '}
            <span style={{ color: '#F9FAFB', fontWeight: 500 }}>
              {diagnostic.students?.email}
            </span>{' '}
            {r.pendingBody2}
          </p>

          <div
            className="inline-block glass rounded-full mt-8"
            style={{ padding: '8px 16px', fontSize: '0.75rem', color: '#6B7280' }}
          >
            ID: {id}
          </div>

          <div className="flex justify-center">
            <CopyLinkButton id={id} />
          </div>

          <div className="flex items-center justify-center gap-2 mt-6">
            <span className="dot-pulse" />
            <span className="dot-pulse" />
            <span className="dot-pulse" />
          </div>
        </div>
      </div>
    )
  }

  if (diagnostic.status === 'rejected') {
    return (
      <div
        className="min-h-screen flex items-center justify-center px-4"
        style={{ background: '#0A0E1A' }}
      >
        <div className="text-center" style={{ maxWidth: '420px' }}>
          <div
            className="mx-auto mb-6 flex items-center justify-center"
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '9999px',
              background: 'rgba(217,119,6,0.1)',
              border: '1px solid rgba(217,119,6,0.3)',
            }}
          >
            <span style={{ color: '#D97706', fontSize: '1.875rem' }}>!</span>
          </div>

          <h1
            className="font-bold"
            style={{
              fontSize: '1.875rem',
              color: '#F9FAFB',
              letterSpacing: '-0.02em',
              marginTop: '24px',
            }}
          >
            Results not available
          </h1>

          <p
            className="mt-4 leading-relaxed"
            style={{ color: '#9CA3AF', fontSize: '0.9375rem', maxWidth: '420px' }}
          >
            This diagnostic was reviewed and cannot be released as a completed report.
          </p>

          <div
            className="inline-block glass rounded-full mt-8"
            style={{ padding: '8px 16px', fontSize: '0.75rem', color: '#6B7280' }}
          >
            ID: {id}
          </div>
        </div>
      </div>
    )
  }

  const score = diagnostic.overall_score ?? 0
  const dims = diagnostic.dimension_scores
  const { label, sub } = scoreLabel(score)
  const color = scoreColor(score)
  const displayName = studentDisplayName(diagnostic)

  const circumference = 2 * Math.PI * 54
  const dashOffset = circumference * (1 - score / 100)

  return (
    <div style={{ background: '#0A0E1A', minHeight: '100vh' }}>
      <div className="max-w-3xl mx-auto px-4 py-16">

        {/* Section 1 — Hero score */}
        <div className="text-center animate-fade-up" style={{ paddingBottom: '64px' }}>
          <p className="animate-fade-up" style={{ color: '#9CA3AF', fontSize: '1.125rem' }}>
            {r.greeting} {displayName.split(' ')[0]}.
          </p>

          <div className="flex justify-center mt-8 animate-fade-up delay-1">
            <svg width="180" height="180" viewBox="0 0 120 120">
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#14B8A6" />
                  <stop offset="100%" stopColor="#0D9488" />
                </linearGradient>
              </defs>
              <circle cx="60" cy="60" r="54" fill="none" stroke="#1A2030" strokeWidth="8" />
              <circle
                cx="60"
                cy="60"
                r="54"
                fill="none"
                stroke="url(#scoreGradient)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${circumference}`}
                strokeDashoffset={`${dashOffset}`}
                style={{ transform: 'rotate(-90deg)', transformOrigin: '60px 60px' }}
              />
              <text
                x="60"
                y="56"
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#F9FAFB"
                fontSize="22"
                fontWeight="700"
                fontFamily="system-ui"
              >
                {score}
              </text>
              <text
                x="60"
                y="74"
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#9CA3AF"
                fontSize="11"
                fontFamily="system-ui"
              >
                /100
              </text>
            </svg>
          </div>

          <div className="mt-4 animate-fade-up delay-2">
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
              <ScoreTierIcon score={score} />
            </div>
            <p className="font-bold text-2xl mt-2" style={{ color, letterSpacing: '-0.02em' }}>
              {label}
            </p>
            <p className="text-sm mt-1" style={{ color: '#9CA3AF' }}>
              {sub}
            </p>
          </div>

          {diagnostic.summary && (
            <p
              className="mx-auto mt-6 leading-relaxed animate-fade-up delay-3"
              style={{ color: '#9CA3AF', fontSize: '1.0625rem', maxWidth: '560px' }}
            >
              {diagnostic.summary}
            </p>
          )}

          <div
            className="animate-fade-up delay-3"
            style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '20px' }}
          >
            <a
              href={`/tracker/${id}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--accent)',
                color: 'white',
                padding: '12px 28px',
                borderRadius: '9999px',
                fontWeight: 600,
                textDecoration: 'none',
                fontSize: '14px',
              }}
            >
              <ClipboardList size={18} /> Open my tracker →
            </a>
            {diagnostic.students?.pathway === 'ausbildung' && (
              <a
                href={`/matches/${id}`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: 'rgba(217,119,6,0.12)',
                  border: '1px solid rgba(217,119,6,0.35)',
                  color: '#D97706',
                  padding: '12px 28px',
                  borderRadius: '9999px',
                  fontWeight: 600,
                  textDecoration: 'none',
                  fontSize: '14px',
                }}
              >
                <Target size={18} /> View matched positions →
              </a>
            )}
          </div>

          <DocumentFactoryClient diagnosticId={id} documentsUnlocked={diagnostic.documents_unlocked ?? false} />
        </div>

        {/* Section 2 — Dimension scores */}
        {dims && (
          <div style={{ paddingBottom: '64px' }}>
            <h2
              className="font-bold mb-8 animate-fade-up delay-2"
              style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
            >
              {r.yourScores}
            </h2>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {DIMENSIONS.map(({ key, label: dimLabel }, index) => {
                const val = dims[key] ?? 0
                const c = scoreColor(val)
                const delayClass = `delay-${index + 1}` as
                  | 'delay-1' | 'delay-2' | 'delay-3' | 'delay-4' | 'delay-5' | 'delay-6'
                return (
                  <div
                    key={key}
                    className={`glass rounded-2xl animate-fade-up ${delayClass}`}
                    style={{ padding: '24px' }}
                  >
                    <div
                      className="font-bold mt-2"
                      style={{ fontSize: '1.875rem', color: c }}
                    >
                      {val}
                    </div>
                    <div className="text-sm mt-1" style={{ color: '#9CA3AF' }}>
                      {dimLabel}
                    </div>
                    <div
                      className="rounded-full overflow-hidden mt-3"
                      style={{ height: '6px', background: '#1A2030' }}
                    >
                      <div
                        style={
                          {
                            height: '100%',
                            borderRadius: '9999px',
                            background: c,
                            '--target-width': `${val}%`,
                            animation: `fillBar 1s ease forwards`,
                            animationDelay: `${0.3 + index * 0.1}s`,
                            width: '0%',
                          } as React.CSSProperties
                        }
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Section 3 — Roadmap */}
        {diagnostic.roadmap && diagnostic.roadmap.length > 0 && (
          <div style={{ paddingBottom: '64px' }}>
            <h2
              className="font-bold mb-2 animate-fade-up"
              style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
            >
              {r.yourRoadmap}
            </h2>
            <p className="mb-8 animate-fade-up" style={{ color: '#9CA3AF' }}>
              {r.roadmapSub}
            </p>

            <div style={{ position: 'relative' }}>
              {diagnostic.roadmap.map((step, i) => (
                <div
                  key={i}
                  className={`animate-fade-up delay-${Math.min(i + 1, 8) as 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8}`}
                  style={{ position: 'relative', paddingLeft: '48px', paddingBottom: '32px' }}
                >
                  {i < (diagnostic.roadmap?.length ?? 0) - 1 && (
                    <div
                      style={{
                        position: 'absolute',
                        left: '15px',
                        top: '28px',
                        bottom: 0,
                        width: '2px',
                        background: '#1A2030',
                      }}
                    />
                  )}

                  <div
                    className="flex items-center justify-center font-bold"
                    style={{
                      position: 'absolute',
                      left: '4px',
                      top: '4px',
                      width: '24px',
                      height: '24px',
                      borderRadius: '9999px',
                      background: 'var(--accent)',
                      color: 'white',
                      fontSize: '0.65rem',
                    }}
                  >
                    {step.month}
                  </div>

                  <div className="glass rounded-xl" style={{ padding: '20px' }}>
                    <div
                      className="uppercase tracking-wider"
                      style={{ fontSize: '0.6875rem', color: '#6B7280', marginBottom: '4px' }}
                    >
                      Month {step.month}
                    </div>
                    <h3
                      className="font-semibold"
                      style={{ color: '#F9FAFB', fontSize: '1.0625rem' }}
                    >
                      {step.title}
                    </h3>
                    <p
                      className="mt-2 leading-relaxed"
                      style={{ color: '#9CA3AF', fontSize: '0.9375rem' }}
                    >
                      {step.description}
                    </p>
                    {step.action_items && step.action_items.length > 0 && (
                      <ul className="mt-3 space-y-1">
                        {step.action_items.map((item, j) => (
                          <li
                            key={j}
                            className="flex gap-2 text-sm"
                            style={{ color: '#9CA3AF' }}
                          >
                            <span
                              style={{
                                width: '6px',
                                height: '6px',
                                borderRadius: '9999px',
                                background: 'var(--accent)',
                                marginTop: '6px',
                                flexShrink: 0,
                              }}
                            />
                            {item}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section 4 — Recommendations */}
        {diagnostic.recommendations && diagnostic.recommendations.length > 0 && (
          <div style={{ paddingBottom: '64px' }}>
            <h2
              className="font-bold mb-8 animate-fade-up"
              style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
            >
              {r.recommended}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {diagnostic.recommendations.map((rec, i) => (
                <div
                  key={i}
                  className={`glass rounded-2xl animate-fade-up delay-${Math.min(i + 1, 3) as 1 | 2 | 3}`}
                  style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}
                >
                  <span
                    className="rounded-full text-xs font-medium inline-block self-start mb-4"
                    style={{
                      background: 'var(--accent-dim)',
                      color: 'var(--accent-light)',
                      border: '1px solid rgba(13,148,136,0.2)',
                      padding: '3px 12px',
                    }}
                  >
                    {rec.type}
                  </span>
                  <h3 className="font-semibold" style={{ color: '#F9FAFB', fontSize: '1rem' }}>
                    {rec.name}
                  </h3>
                  <p
                    className="mt-2 leading-relaxed flex-1"
                    style={{ color: '#9CA3AF', fontSize: '0.875rem' }}
                  >
                    {rec.description}
                  </p>
                  {rec.url && (
                    <a
                      href={rec.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-4 block text-sm hover:underline"
                      style={{ color: 'var(--accent-light)' }}
                    >
                      Visit →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section 5 — CTA */}
        <div
          className="text-center animate-fade-up"
          style={{ paddingTop: '48px', paddingBottom: '48px' }}
        >
          <h2
            className="font-bold"
            style={{ fontSize: '1.5rem', color: '#F9FAFB', letterSpacing: '-0.02em' }}
          >
            {r.ctaTitle}
          </h2>
          <p className="mt-2 mb-6" style={{ color: '#9CA3AF' }}>
            {diagnostic.next_step_message ?? r.ctaBody}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <ShareButton id={id} />
            <a
              href="https://cal.com/lucas-barrios-qlrx5k/free-15-min-germany-pathway-consultation"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold rounded-full transition-all cta-button"
              style={{
                background: 'var(--accent)',
                color: 'white',
                padding: '12px 24px',
                textDecoration: 'none',
              }}
            >
              {r.bookBtn}
            </a>
            <DownloadPdfButton
              studentName={displayName}
              diagnostic={diagnostic}
            />
          </div>
        </div>

        <p
          className="text-xs text-center mt-8 pb-8"
          style={{ color: '#6B7280' }}
        >
          {r.disclaimer}
        </p>
      </div>
    </div>
  )
}
