'use client'

import { useState, useEffect, useCallback } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL

type DimensionScores = {
  language: number
  education: number
  pathway_fit: number
  timeline: number
  financial: number
  documentation: number
}

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

type DiagnosticRow = {
  id: string
  created_at: string
  status: string
  overall_score: number | null
  summary: string | null
  dimension_scores: DimensionScores | null
  roadmap: RoadmapStep[] | null
  recommendations: Recommendation[] | null
  students: {
    name: string
    email: string
    country: string
    pathway: string
    german_level: string
    education_level?: string
    timeline: string
  } | null
}

const DIMENSION_LABELS: { key: keyof DimensionScores; label: string }[] = [
  { key: 'language', label: 'Language' },
  { key: 'education', label: 'Education' },
  { key: 'pathway_fit', label: 'Pathway Fit' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'financial', label: 'Financial' },
  { key: 'documentation', label: 'Documentation' },
]

function scoreColor(val: number): string {
  if (val < 40) return '#EF4444'
  if (val < 60) return '#F59E0B'
  if (val < 80) return '#3B82F6'
  return '#0D9488'
}

function scoreLabel(score: number): string {
  if (score < 40) return 'Not ready'
  if (score < 60) return 'Early stage'
  if (score < 80) return 'Good fit'
  return 'Strong candidate'
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${Math.max(1, mins)} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function PathwayBadge({ pathway }: { pathway: string }) {
  const map: Record<string, { bg: string; color: string; border: string; label: string }> = {
    ausbildung: {
      bg: 'rgba(245,158,11,0.1)',
      color: '#F59E0B',
      border: 'rgba(245,158,11,0.2)',
      label: 'Ausbildung',
    },
    university: {
      bg: 'rgba(59,130,246,0.1)',
      color: '#3B82F6',
      border: 'rgba(59,130,246,0.2)',
      label: 'University',
    },
    work_visa: {
      bg: 'rgba(139,92,246,0.1)',
      color: '#8B5CF6',
      border: 'rgba(139,92,246,0.2)',
      label: 'Work Visa',
    },
  }
  const s = map[pathway] ?? map.university
  return (
    <span
      style={{
        background: s.bg,
        color: s.color,
        border: `1px solid ${s.border}`,
        borderRadius: '9999px',
        padding: '2px 8px',
        fontSize: '0.75rem',
        fontWeight: 500,
      }}
    >
      {s.label}
    </span>
  )
}

function Toast({
  message,
  type,
  onDone,
}: {
  message: string
  type: 'success' | 'error'
  onDone: () => void
}) {
  useEffect(() => {
    const t = setTimeout(onDone, 3000)
    return () => clearTimeout(t)
  }, [onDone])

  return (
    <div
      style={{
        position: 'fixed',
        top: '24px',
        right: '24px',
        zIndex: 60,
        background:
          type === 'success' ? 'rgba(13,148,136,0.15)' : 'rgba(239,68,68,0.15)',
        border: `1px solid ${type === 'success' ? 'rgba(13,148,136,0.4)' : 'rgba(239,68,68,0.4)'}`,
        color: type === 'success' ? '#2DD4BF' : '#F87171',
        padding: '12px 20px',
        borderRadius: '12px',
        backdropFilter: 'blur(12px)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        animation: 'slideInToast 0.3s ease forwards',
        fontSize: '0.875rem',
        minWidth: '240px',
      }}
    >
      {message}
    </div>
  )
}

function PasswordScreen({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState('')
  const [pwError, setPwError] = useState(false)

  function handleLogin() {
    if (password === 'klar2026') {
      onLogin()
    } else {
      setPwError(true)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0A0E1A',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
    >
      <div
        style={{
          fontSize: '1.875rem',
          fontWeight: 700,
          color: '#F9FAFB',
          letterSpacing: '-0.02em',
          marginBottom: '32px',
        }}
      >
        Klar 🇩🇪
      </div>

      <div
        className="glass"
        style={{
          borderRadius: '16px',
          padding: '32px',
          width: '100%',
          maxWidth: '380px',
        }}
      >
        <h1
          style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: '#F9FAFB',
            letterSpacing: '-0.02em',
            marginBottom: '4px',
          }}
        >
          Consultant Access
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#6B7280', marginBottom: '24px' }}>
          This area is for Klar advisors only.
        </p>

        <input
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            setPwError(false)
          }}
          onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
          placeholder="Enter password"
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: `2px solid ${pwError ? '#EF4444' : '#1F2937'}`,
            color: '#F9FAFB',
            fontSize: '1.125rem',
            padding: '8px 0',
            width: '100%',
            outline: 'none',
          }}
          onFocus={(e) => (e.target.style.borderBottomColor = '#3B82F6')}
          onBlur={(e) =>
            (e.target.style.borderBottomColor = pwError ? '#EF4444' : '#1F2937')
          }
        />

        {pwError && (
          <p style={{ fontSize: '0.75rem', color: '#EF4444', marginTop: '8px' }}>
            Incorrect password. Try again.
          </p>
        )}

        <button
          onClick={handleLogin}
          className="cta-button"
          style={{
            background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            padding: '12px',
            width: '100%',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: 'pointer',
            marginTop: '16px',
            minHeight: '44px',
          }}
        >
          Access dashboard →
        </button>
      </div>
    </div>
  )
}

function DetailsPanel({
  row,
  notes,
  onNotesChange,
  onClose,
  onApprove,
  onReject,
}: {
  row: DiagnosticRow
  notes: string
  onNotesChange: (v: string) => void
  onClose: () => void
  onApprove: (id: string, notes: string) => Promise<void>
  onReject: (id: string, notes: string) => Promise<void>
}) {
  const [busy, setBusy] = useState(false)
  const [roadmapOpen, setRoadmapOpen] = useState(false)

  async function act(fn: (id: string, n: string) => Promise<void>) {
    setBusy(true)
    await fn(row.id, notes)
    setBusy(false)
  }

  const score = row.overall_score

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 50,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
        }}
      />
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          position: 'fixed',
          right: 0,
          top: 0,
          bottom: 0,
          zIndex: 50,
          width: 'min(520px, 100vw)',
          background: '#111827',
          borderLeft: '1px solid #1F2937',
          overflowY: 'auto',
          padding: '24px',
          animation: 'slideInPanel 0.3s ease forwards',
        }}
      >
        <button
          onClick={onClose}
          className="glass"
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            width: '32px',
            height: '32px',
            borderRadius: '9999px',
            border: 'none',
            color: '#F9FAFB',
            fontSize: '18px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            lineHeight: 1,
          }}
        >
          ×
        </button>

        <div style={{ marginTop: '8px' }}>
          <h2
            style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: '#F9FAFB',
              letterSpacing: '-0.02em',
            }}
          >
            {row.students?.name}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>
            {row.students?.email}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>
              🌍 {row.students?.country}
            </span>
            {row.students?.pathway && <PathwayBadge pathway={row.students.pathway} />}
          </div>
        </div>

        {score !== null && score !== undefined && (
          <div className="glass" style={{ borderRadius: '16px', padding: '20px', marginTop: '24px' }}>
            <p
              style={{
                fontSize: '0.75rem',
                color: '#6B7280',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                marginBottom: '12px',
              }}
            >
              Overall Score
            </p>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
              <span className="gradient-text" style={{ fontSize: '3rem', fontWeight: 700, lineHeight: 1 }}>
                {score}
              </span>
              <span style={{ fontSize: '1.25rem', color: '#9CA3AF', marginBottom: '4px' }}>/100</span>
            </div>
            <span
              style={{
                display: 'inline-block',
                borderRadius: '9999px',
                fontSize: '0.75rem',
                fontWeight: 500,
                marginTop: '8px',
                padding: '2px 10px',
                background: `${scoreColor(score)}22`,
                color: scoreColor(score),
                border: `1px solid ${scoreColor(score)}44`,
              }}
            >
              {scoreLabel(score)}
            </span>

            {row.dimension_scores && (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  marginTop: '16px',
                }}
              >
                {DIMENSION_LABELS.map(({ key, label }) => {
                  const val = row.dimension_scores![key] ?? 0
                  return (
                    <div key={key}>
                      <p style={{ fontSize: '0.75rem', color: '#6B7280', marginBottom: '4px' }}>
                        {label}
                      </p>
                      <p style={{ fontSize: '1.125rem', fontWeight: 700, color: scoreColor(val) }}>
                        {val}
                      </p>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {row.summary && (
          <div className="glass" style={{ borderRadius: '16px', padding: '20px', marginTop: '16px' }}>
            <p
              style={{
                fontSize: '0.75rem',
                color: '#6B7280',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                marginBottom: '12px',
              }}
            >
              AI Summary
            </p>
            <p style={{ fontSize: '0.875rem', color: '#9CA3AF', lineHeight: 1.6 }}>
              {row.summary}
            </p>
          </div>
        )}

        <div style={{ marginTop: '16px' }}>
          <label
            style={{
              display: 'block',
              fontSize: '0.875rem',
              color: '#9CA3AF',
              marginBottom: '8px',
            }}
          >
            Reviewer notes (optional)
          </label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Add any notes for this student..."
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid #1F2937',
              borderRadius: '12px',
              color: '#F9FAFB',
              fontSize: '0.875rem',
              outline: 'none',
              padding: '12px',
              resize: 'none',
              width: '100%',
            }}
            onFocus={(e) => (e.target.style.borderColor = '#3B82F6')}
            onBlur={(e) => (e.target.style.borderColor = '#1F2937')}
          />
        </div>

        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '24px' }}
        >
          <button
            onClick={() => act(onReject)}
            disabled={busy}
            style={{
              background: 'transparent',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: '12px',
              color: '#EF4444',
              fontSize: '0.875rem',
              fontWeight: 500,
              padding: '12px',
              cursor: busy ? 'not-allowed' : 'pointer',
              opacity: busy ? 0.5 : 1,
              minHeight: '44px',
              transition: 'background 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (!busy) e.currentTarget.style.background = 'rgba(239,68,68,0.1)'
            }}
            onMouseLeave={(e) => {
              if (!busy) e.currentTarget.style.background = 'transparent'
            }}
          >
            ✕ Reject
          </button>
          <button
            onClick={() => act(onApprove)}
            disabled={busy}
            style={{
              background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
              border: 'none',
              borderRadius: '12px',
              color: 'white',
              fontSize: '0.875rem',
              fontWeight: 600,
              padding: '12px',
              cursor: busy ? 'not-allowed' : 'pointer',
              opacity: busy ? 0.5 : 1,
              minHeight: '44px',
              transition: 'filter 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (!busy) e.currentTarget.style.filter = 'brightness(1.1)'
            }}
            onMouseLeave={(e) => {
              if (!busy) e.currentTarget.style.filter = 'brightness(1)'
            }}
          >
            ✓ Approve
          </button>
        </div>

        {row.roadmap && row.roadmap.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <button
              onClick={() => setRoadmapOpen((o) => !o)}
              className="glass"
              style={{
                borderRadius: '12px',
                padding: '16px',
                width: '100%',
                textAlign: 'left',
                cursor: 'pointer',
                border: 'none',
              }}
            >
              <span style={{ fontSize: '0.875rem', fontWeight: 500, color: '#9CA3AF' }}>
                {roadmapOpen ? '▲' : '▼'} View roadmap ({row.roadmap.length} steps)
              </span>
            </button>

            {roadmapOpen && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                {row.roadmap.slice(0, 3).map((step, i) => (
                  <div
                    key={i}
                    className="glass"
                    style={{
                      borderRadius: '12px',
                      padding: '16px',
                      display: 'flex',
                      gap: '12px',
                    }}
                  >
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '9999px',
                        background: 'rgba(59,130,246,0.15)',
                        color: '#3B82F6',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      M{step.month}
                    </div>
                    <div>
                      <p
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: '#F9FAFB',
                          marginBottom: '4px',
                        }}
                      >
                        {step.title}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6B7280' }}>{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}

function DiagnosticCard({
  row,
  onView,
  onApprove,
  onReject,
}: {
  row: DiagnosticRow
  onView: () => void
  onApprove: (id: string) => void
  onReject: (id: string) => void
}) {
  const score = row.overall_score

  return (
    <div
      className="glass"
      style={{ borderRadius: '16px', padding: '20px', marginBottom: '16px' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ fontSize: '1.125rem', fontWeight: 600, color: '#F9FAFB' }}>
            {row.students?.name}
          </p>
          <div
            style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}
          >
            <span>🌍</span>
            <span style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>{row.students?.country}</span>
            <span style={{ color: '#6B7280' }}>·</span>
            {row.students?.pathway && <PathwayBadge pathway={row.students.pathway} />}
          </div>
        </div>
        <span
          className="glass"
          style={{
            borderRadius: '9999px',
            padding: '4px 12px',
            fontSize: '0.75rem',
            color: '#6B7280',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          {timeAgo(row.created_at)}
        </span>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
        {row.students?.german_level && (
          <span
            className="glass"
            style={{ borderRadius: '9999px', padding: '4px 12px', fontSize: '0.75rem', color: '#9CA3AF' }}
          >
            🗣️ {row.students.german_level}
          </span>
        )}
        {row.students?.education_level && (
          <span
            className="glass"
            style={{ borderRadius: '9999px', padding: '4px 12px', fontSize: '0.75rem', color: '#9CA3AF' }}
          >
            🎓 {row.students.education_level}
          </span>
        )}
        {row.students?.timeline && (
          <span
            className="glass"
            style={{ borderRadius: '9999px', padding: '4px 12px', fontSize: '0.75rem', color: '#9CA3AF' }}
          >
            ⏱️ {row.students.timeline}
          </span>
        )}
        {row.students?.email && (
          <span
            className="glass"
            style={{ borderRadius: '9999px', padding: '4px 12px', fontSize: '0.75rem', color: '#9CA3AF' }}
          >
            📧 {row.students.email}
          </span>
        )}
      </div>

      {score !== null && score !== undefined && (
        <div style={{ marginTop: '12px' }}>
          <div
            style={{
              height: '6px',
              background: '#1F2937',
              borderRadius: '9999px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${score}%`,
                background: scoreColor(score),
                borderRadius: '9999px',
                transition: 'width 0.5s ease',
              }}
            />
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '4px',
            }}
          >
            <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>Score: {score}/100</span>
            <span style={{ fontSize: '0.75rem', color: scoreColor(score) }}>{scoreLabel(score)}</span>
          </div>
        </div>
      )}

      <div
        style={{
          display: 'flex',
          gap: '8px',
          justifyContent: 'flex-end',
          marginTop: '16px',
          flexWrap: 'wrap',
        }}
      >
        <button
          onClick={onView}
          className="glass"
          style={{
            borderRadius: '9999px',
            padding: '8px 16px',
            fontSize: '0.875rem',
            color: '#9CA3AF',
            cursor: 'pointer',
            minHeight: '44px',
            transition: 'color 0.15s ease',
            border: 'none',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#F9FAFB')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#9CA3AF')}
        >
          View details
        </button>
        <button
          onClick={() => onReject(row.id)}
          style={{
            background: 'transparent',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: '9999px',
            color: '#EF4444',
            fontSize: '0.875rem',
            padding: '8px 16px',
            cursor: 'pointer',
            minHeight: '44px',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(239,68,68,0.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          ✕ Reject
        </button>
        <button
          onClick={() => onApprove(row.id)}
          style={{
            background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
            border: 'none',
            borderRadius: '9999px',
            color: 'white',
            fontSize: '0.875rem',
            fontWeight: 600,
            padding: '8px 20px',
            cursor: 'pointer',
            minHeight: '44px',
            transition: 'filter 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.filter = 'brightness(1.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.filter = 'brightness(1)')}
        >
          ✓ Approve
        </button>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const [authed, setAuthed] = useState(false)
  const [rows, setRows] = useState<DiagnosticRow[]>([])
  const [loadingRows, setLoadingRows] = useState(false)
  const [selected, setSelected] = useState<DiagnosticRow | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [activeFilter, setActiveFilter] = useState('all')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [stats, setStats] = useState({ pending: 0, approved_today: 0, total: 0 })

  const fetchRows = useCallback(async () => {
    setLoadingRows(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/diagnostics`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      setRows(data)
    } catch {
      // silently fail on load
    } finally {
      setLoadingRows(false)
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/stats`)
      if (!res.ok) return
      const data = await res.json()
      setStats(data)
    } catch {
      // silently fail
    }
  }, [])

  useEffect(() => {
    if (authed) {
      fetchRows()
      fetchStats()
    }
  }, [authed, fetchRows, fetchStats])

  async function handleReview(id: string, status: 'approved' | 'rejected', reviewerNotes: string) {
    const res = await fetch(`${API_URL}/api/admin/diagnostics/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, reviewer_notes: reviewerNotes }),
    })
    if (res.ok) {
      setRows((prev) => prev.filter((r) => r.id !== id))
      setSelected(null)
      setToast(
        status === 'approved'
          ? { message: '✓ Approved — student will be notified', type: 'success' }
          : { message: '✕ Rejected', type: 'error' }
      )
    }
  }

  const hour = new Date().getHours()
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const dateStr = new Date().toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  const filters = [
    { key: 'all', label: 'All' },
    { key: 'ausbildung', label: 'Ausbildung' },
    { key: 'university', label: 'University' },
    { key: 'work_visa', label: 'Work Visa' },
  ]

  const filteredRows =
    activeFilter === 'all'
      ? rows
      : rows.filter((r) => r.students?.pathway === activeFilter)

  if (!authed) {
    return <PasswordScreen onLogin={() => setAuthed(true)} />
  }

  return (
    <div style={{ background: '#0A0E1A', minHeight: '100vh' }}>
      <div
        style={{
          maxWidth: '900px',
          margin: '0 auto',
          padding: '32px 16px 48px',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '32px',
          }}
        >
          <div>
            <h1
              style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: '#F9FAFB',
                letterSpacing: '-0.02em',
              }}
            >
              {greeting}, Cleo 👋
            </h1>
            <p style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>
              {dateStr}
            </p>
          </div>
          <button
            onClick={() => setAuthed(false)}
            className="glass"
            style={{
              borderRadius: '9999px',
              padding: '8px 16px',
              fontSize: '0.875rem',
              color: '#6B7280',
              cursor: 'pointer',
              minHeight: '44px',
              transition: 'color 0.15s ease',
              border: 'none',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#F9FAFB')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#6B7280')}
          >
            Sign out
          </button>
        </div>

        {/* Stats bar */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '16px',
            marginBottom: '32px',
          }}
        >
          <div className="glass" style={{ borderRadius: '16px', padding: '20px' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>📥</div>
            <div className="gradient-text" style={{ fontSize: '1.875rem', fontWeight: 700 }}>
              {loadingRows ? '—' : String(stats.pending)}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>
              Pending review
            </div>
          </div>

          <div className="glass" style={{ borderRadius: '16px', padding: '20px' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>✅</div>
            <div className="gradient-text" style={{ fontSize: '1.875rem', fontWeight: 700 }}>
              {loadingRows ? '—' : String(stats.approved_today)}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>
              Approved today
            </div>
          </div>

          <div className="glass" style={{ borderRadius: '16px', padding: '20px' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>⚡</div>
            <div className="gradient-text" style={{ fontSize: '1.875rem', fontWeight: 700 }}>
              {loadingRows ? '—' : String(stats.total)}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>
              all time
            </div>
            <div style={{ fontSize: '0.75rem', color: '#4B5563', marginTop: '2px' }}>
              ~2 min avg review
            </div>
          </div>
        </div>

        {/* Filter tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => setActiveFilter(f.key)}
              style={{
                borderRadius: '9999px',
                padding: '6px 16px',
                fontSize: '0.875rem',
                cursor: 'pointer',
                minHeight: '36px',
                transition: 'all 0.15s ease',
                background:
                  activeFilter === f.key ? '#3B82F6' : 'rgba(255,255,255,0.04)',
                color: activeFilter === f.key ? 'white' : '#9CA3AF',
                border:
                  activeFilter === f.key
                    ? 'none'
                    : '1px solid rgba(255,255,255,0.08)',
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Diagnostics list */}
        {loadingRows ? (
          <div
            className="glass"
            style={{
              borderRadius: '16px',
              padding: '48px',
              textAlign: 'center',
              color: '#6B7280',
            }}
          >
            Loading...
          </div>
        ) : filteredRows.length === 0 ? (
          <div
            className="glass"
            style={{
              borderRadius: '16px',
              padding: '64px 32px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>🎉</div>
            <p
              style={{
                fontSize: '1.25rem',
                fontWeight: 700,
                color: '#F9FAFB',
                marginBottom: '8px',
              }}
            >
              All caught up!
            </p>
            <p style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>
              No diagnostics pending review.
            </p>
          </div>
        ) : (
          <div>
            {filteredRows.map((row) => (
              <DiagnosticCard
                key={row.id}
                row={row}
                onView={() => setSelected(row)}
                onApprove={(id) => handleReview(id, 'approved', notes[id] ?? '')}
                onReject={(id) => handleReview(id, 'rejected', notes[id] ?? '')}
              />
            ))}
          </div>
        )}
      </div>

      {selected && (
        <DetailsPanel
          row={selected}
          notes={notes[selected.id] ?? ''}
          onNotesChange={(v) =>
            setNotes((prev) => ({ ...prev, [selected.id]: v }))
          }
          onClose={() => setSelected(null)}
          onApprove={(id, n) => handleReview(id, 'approved', n)}
          onReject={(id, n) => handleReview(id, 'rejected', n)}
        />
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  )
}
