'use client'
import { useState, useEffect } from 'react'

const DEMO = {
  name: 'Carlos M.',
  country: '🇲🇽 Mexico',
  pathway: 'Ausbildung',
  overall_score: 68,
  score_label: 'Ready with preparation',
  summary:
    'Carlos has a strong educational background and clear pathway alignment. The main focus areas are German language level and financial documentation before applying.',
  dimensions: [
    { key: 'language', label: 'German Language', score: 55 },
    { key: 'education', label: 'Education', score: 72 },
    { key: 'pathway_fit', label: 'Pathway Fit', score: 80 },
    { key: 'financial', label: 'Finances', score: 48 },
    { key: 'timeline', label: 'Timeline', score: 71 },
    { key: 'documentation', label: 'Documentation', score: 62 },
  ],
}

function scoreColor(val: number): string {
  if (val < 40) return '#EF4444'
  if (val < 60) return '#F59E0B'
  if (val < 80) return '#3B82F6'
  return '#0D9488'
}

export default function DiagnosticPreviewCard() {
  const [animated, setAnimated] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(t)
  }, [])

  const r = 38
  const circumference = 2 * Math.PI * r
  const targetOffset = circumference * (1 - DEMO.overall_score / 100)
  const ringColor = scoreColor(DEMO.overall_score)

  return (
    <div
      style={{
        transform: 'rotate(-2deg)',
        transition: 'transform 0.3s ease',
        display: 'inline-block',
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.transform =
          'rotate(0deg) translateY(-4px)'
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.transform = 'rotate(-2deg)'
      }}
    >
      <div
        style={{
          background: 'rgba(17, 24, 39, 0.85)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '20px',
          padding: '24px',
          boxShadow:
            '0 24px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05), 0 0 80px rgba(37,99,235,0.08)',
          width: '340px',
          animation: 'cardFadeIn 0.6s ease 0.2s both',
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: '16px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '12px',
            }}
          >
            <div>
              <div
                style={{ fontSize: '14px', fontWeight: 700, color: 'white', marginBottom: '2px' }}
              >
                {DEMO.name}
              </div>
              <div style={{ fontSize: '12px', color: '#9CA3AF' }}>{DEMO.country}</div>
            </div>
            <span
              style={{
                background: 'rgba(13,148,136,0.15)',
                border: '1px solid rgba(13,148,136,0.3)',
                color: '#14B8A6',
                borderRadius: '9999px',
                fontSize: '11px',
                padding: '2px 8px',
              }}
            >
              {DEMO.pathway}
            </span>
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />
        </div>

        {/* Score ring */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
          <div style={{ position: 'relative', width: 96, height: 96 }}>
            <svg width={96} height={96} style={{ transform: 'rotate(-90deg)' }}>
              <circle
                cx={48}
                cy={48}
                r={r}
                fill="none"
                stroke="rgba(255,255,255,0.06)"
                strokeWidth={6}
              />
              <circle
                cx={48}
                cy={48}
                r={r}
                fill="none"
                stroke={ringColor}
                strokeWidth={6}
                strokeDasharray={circumference}
                strokeDashoffset={animated ? targetOffset : circumference}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 1s ease-out' }}
              />
            </svg>
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{ fontSize: '28px', fontWeight: 700, color: 'white', lineHeight: 1 }}
              >
                {DEMO.overall_score}
              </div>
              <div
                style={{
                  fontSize: '11px',
                  color: '#9CA3AF',
                  marginTop: '2px',
                  textAlign: 'center',
                  maxWidth: '72px',
                  lineHeight: 1.3,
                }}
              >
                {DEMO.score_label}
              </div>
            </div>
          </div>
        </div>

        {/* Dimension bars */}
        <div
          style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}
        >
          {DEMO.dimensions.map(({ key, label, score }, i) => {
            const color = scoreColor(score)
            return (
              <div key={key}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '3px',
                  }}
                >
                  <span style={{ fontSize: '10px', color: '#6B7280' }}>{label}</span>
                  <span style={{ fontSize: '10px', color }}>{score}</span>
                </div>
                <div
                  style={{
                    height: '4px',
                    background: 'rgba(255,255,255,0.06)',
                    borderRadius: '2px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: animated ? `${score}%` : '0%',
                      background: color,
                      borderRadius: '2px',
                      transition: `width 0.6s ease ${0.1 * i + 0.1}s`,
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary */}
        <div
          style={{
            borderTop: '1px solid rgba(255,255,255,0.06)',
            paddingTop: '12px',
            marginBottom: '12px',
          }}
        >
          <p
            style={{
              fontSize: '11px',
              color: '#9CA3AF',
              lineHeight: 1.5,
              overflow: 'hidden',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {DEMO.summary}
          </p>
        </div>

        {/* Reviewed badge */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <span
            style={{
              background: 'rgba(13,148,136,0.1)',
              color: '#14B8A6',
              fontSize: '10px',
              borderRadius: '9999px',
              padding: '3px 10px',
            }}
          >
            ✓ Reviewed by consultant
          </span>
        </div>
      </div>
    </div>
  )
}
