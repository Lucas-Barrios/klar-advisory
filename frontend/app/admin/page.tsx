'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Inbox, CheckCircle2, Gauge, Globe, Languages, GraduationCap, Clock, Mail } from 'lucide-react'
import GermanFlag from '@/components/GermanFlag'
import { useIsWide } from '@/lib/useIsWide'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const ADMIN_TOKEN_STORAGE_KEY = 'klar_admin_api_token'

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
  next_step_message?: string | null
  consultation_booked?: boolean | null
  dimension_scores: DimensionScores | null
  roadmap: RoadmapStep[] | null
  recommendations: Recommendation[] | null
  students: {
    name?: string | null
    full_name?: string | null
    email?: string | null
    country?: string | null
    pathway?: string | null
    german_level?: string | null
    education_level?: string | null
    timeline?: string | null
  } | null
}

type MatchedPosition = {
  refnr: string
  titel: string | null
  arbeitgeber: string | null
  ort: string | null
  eintrittsdatum: string | null
  application_url: string | null
  fit_explanation: string
  estimated_german_level_needed: string
  german_level_concern: boolean | string
  urgency_note: string
}

type AusbildungMatch = {
  id: string
  status: string
  reasoning_summary: string | null
  matched_positions: MatchedPosition[]
}

type TcoStats = {
  current_month_ai_calls: number
  successful_calls: number
  failed_calls: number
  estimated_cost: number
  forecasted_month_end_cost: number
  average_cost_per_diagnostic: number
  average_latency_ms: number
}

type EvaluationExperimentSummary = {
  id: string
  name: string
  status: string
  baseline_run_id: string
  challenger_run_id: string
  metric_name: string
  summary?: {
    p_value?: number | null
    effect_size?: number | null
    recommendation?: string | null
    warnings?: string[]
  }
  latest_comparison?: {
    metric_name?: string
    baseline_mean?: number | null
    challenger_mean?: number | null
    p_value?: number | null
    effect_size?: number | null
    recommendation?: string | null
    warnings?: string[]
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

const COUNTRY_FLAGS: Record<string, string> = {
  Brazil: '🇧🇷', India: '🇮🇳', China: '🇨🇳', Mexico: '🇲🇽',
  Pakistan: '🇵🇰', Bangladesh: '🇧🇩', Morocco: '🇲🇦', Egypt: '🇪🇬',
  Turkey: '🇹🇷', Colombia: '🇨🇴', Philippines: '🇵🇭', Vietnam: '🇻🇳',
  Indonesia: '🇮🇩', Nigeria: '🇳🇬', Ukraine: '🇺🇦', Peru: '🇵🇪',
  Ethiopia: '🇪🇹', Ghana: '🇬🇭', Kenya: '🇰🇪', Argentina: '🇦🇷',
  Syria: '🇸🇾', Afghanistan: '🇦🇫', Iran: '🇮🇷', Iraq: '🇮🇶',
  'Saudi Arabia': '🇸🇦', Nepal: '🇳🇵', 'Sri Lanka': '🇱🇰',
  Romania: '🇷🇴', Poland: '🇵🇱', Serbia: '🇷🇸', Albania: '🇦🇱',
}

function countryFlag(country: string | null | undefined): string {
  if (!country) return ''
  return COUNTRY_FLAGS[country] ?? '🌍'
}

function barColor(val: number): string {
  if (val >= 70) return '#10B981'
  if (val >= 40) return '#F59E0B'
  return '#EF4444'
}

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
  if (mins < 60) return `${Math.max(1, mins)}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
    minimumFractionDigits: 2, maximumFractionDigits: 4,
  }).format(value)
}

function formatStat(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toFixed(digits)
}

function shortId(value: string | null | undefined): string {
  if (!value) return '—'
  return value.slice(0, 8)
}

function studentDisplayName(student: DiagnosticRow['students']): string {
  return student?.name ?? student?.full_name ?? 'Student'
}

function isAuthFailure(statusCode: number): boolean {
  return statusCode === 401 || statusCode === 403
}

function isReviewed(row: DiagnosticRow): boolean {
  return row.status === 'approved' || row.status === 'rejected'
}


function PathwayBadge({ pathway }: { pathway: string }) {
  const map: Record<string, { bg: string; color: string; border: string; label: string }> = {
    ausbildung: { bg: 'rgba(245,158,11,0.1)', color: '#F59E0B', border: 'rgba(245,158,11,0.2)', label: 'Ausbildung' },
    university: { bg: 'var(--accent-dim)', color: 'var(--accent-light)', border: 'rgba(13,148,136,0.2)', label: 'University' },
    work_visa: { bg: 'rgba(139,92,246,0.1)', color: '#A78BFA', border: 'rgba(139,92,246,0.2)', label: 'Work Visa' },
  }
  const s = map[pathway] ?? map.university
  return (
    <span style={{
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      borderRadius: '9999px', padding: '2px 8px', fontSize: '0.75rem', fontWeight: 500,
    }}>
      {s.label}
    </span>
  )
}

function Toast({ message, type, onDone }: { message: string; type: 'success' | 'error'; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3000)
    return () => clearTimeout(t)
  }, [onDone])
  return (
    <div style={{
      position: 'fixed', top: '24px', right: '24px', zIndex: 60,
      background: type === 'success' ? 'rgba(13,148,136,0.15)' : 'rgba(239,68,68,0.15)',
      border: `1px solid ${type === 'success' ? 'rgba(13,148,136,0.4)' : 'rgba(239,68,68,0.4)'}`,
      color: type === 'success' ? '#2DD4BF' : '#F87171',
      padding: '12px 20px', borderRadius: '12px', backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)', animation: 'slideInToast 0.3s ease forwards',
      fontSize: '0.875rem', minWidth: '240px',
    }}>
      {message}
    </div>
  )
}

function PasswordScreen({ onLogin }: { onLogin: (token: string) => Promise<boolean> }) {
  const [token, setToken] = useState('')
  const [pwError, setPwError] = useState(false)
  const [busy, setBusy] = useState(false)

  async function handleLogin() {
    const trimmedToken = token.trim()
    if (!trimmedToken) { setPwError(true); return }
    setBusy(true)
    const ok = await onLogin(trimmedToken)
    setBusy(false)
    if (!ok) setPwError(true)
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0A0E1A', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div style={{ fontSize: '1.875rem', fontWeight: 700, color: '#F9FAFB', letterSpacing: '-0.02em', marginBottom: '32px' }}>
        Klar <GermanFlag size={28} />
      </div>
      <div className="glass" style={{ borderRadius: '16px', padding: '32px', width: '100%', maxWidth: '380px' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#F9FAFB', letterSpacing: '-0.02em', marginBottom: '4px' }}>
          Consultant Access
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#6B7280', marginBottom: '24px' }}>
          This area is for Klar advisors only.
        </p>
        <input
          type="password" value={token}
          onChange={(e) => { setToken(e.target.value); setPwError(false) }}
          onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
          placeholder="Admin access token"
          style={{
            background: 'transparent', border: 'none',
            borderBottom: `2px solid ${pwError ? '#EF4444' : '#1F2937'}`,
            color: '#F9FAFB', fontSize: '1.125rem', padding: '8px 0', width: '100%', outline: 'none',
          }}
          onFocus={(e) => (e.target.style.borderBottomColor = 'var(--accent)')}
          onBlur={(e) => (e.target.style.borderBottomColor = pwError ? '#EF4444' : '#1F2937')}
        />
        {pwError && <p style={{ fontSize: '0.75rem', color: '#EF4444', marginTop: '8px' }}>Invalid access token. Try again.</p>}
        <button onClick={handleLogin} disabled={busy} className="cta-button" style={{
          background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '12px',
          padding: '12px', width: '100%', fontSize: '0.875rem', fontWeight: 600,
          cursor: busy ? 'wait' : 'pointer', marginTop: '16px', minHeight: '44px', opacity: busy ? 0.7 : 1,
        }}>
          {busy ? 'Checking...' : 'Access dashboard →'}
        </button>
      </div>
    </div>
  )
}

function ScoreRing({ score, size = 72 }: { score: number; size?: number }) {
  const sw = 5
  const r = (size - sw) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - score / 100)
  const color = barColor(score)
  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1F2937" strokeWidth={sw} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={sw}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1rem', fontWeight: 700, color,
      }}>
        {score}
      </div>
    </div>
  )
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = barColor(value)
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <span style={{ fontSize: '0.75rem', color: '#9CA3AF' }}>{label}</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color, minWidth: '28px', textAlign: 'right' }}>{value}</span>
      </div>
      <div style={{ height: '6px', background: '#1F2937', borderRadius: '9999px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${value}%`, background: color, borderRadius: '9999px', transition: 'width 0.4s ease' }} />
      </div>
    </div>
  )
}

function MatchedPositionsSection({ diagnosticId, adminToken }: { diagnosticId: string; adminToken: string }) {
  const [match, setMatch] = useState<AusbildungMatch | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_URL}/api/admin/diagnostics/${diagnosticId}/matches`, {
          headers: { Authorization: `Bearer ${adminToken}` },
        })
        if (res.ok) setMatch(await res.json())
      } catch { /* silently fail */ } finally { setLoading(false) }
    }
    load()
  }, [diagnosticId, adminToken])

  if (loading) return (
    <div className="glass" style={{ borderRadius: '12px', padding: '16px', color: '#6B7280', fontSize: '0.875rem' }}>
      Loading matched positions…
    </div>
  )

  if (!match || !match.matched_positions || match.matched_positions.length === 0) return (
    <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
      <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Matched Positions</p>
      <p style={{ fontSize: '0.875rem', color: '#6B7280' }}>No positions matched yet.</p>
    </div>
  )

  return (
    <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
      <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
        Matched Positions
      </p>
      {match.reasoning_summary && (
        <p style={{ fontSize: '0.8125rem', color: '#9CA3AF', lineHeight: 1.6, marginBottom: '12px' }}>{match.reasoning_summary}</p>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {match.matched_positions.map((pos, i) => {
          const hasConcern = pos.german_level_concern === true || pos.german_level_concern === 'true'
          return (
            <div key={pos.refnr ?? i} style={{ borderRadius: '8px', border: '1px solid #1F2937', padding: '12px', background: 'rgba(255,255,255,0.02)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                <div>
                  <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F9FAFB', margin: 0 }}>{pos.arbeitgeber ?? '—'}</p>
                  <p style={{ fontSize: '0.8125rem', color: '#9CA3AF', marginTop: '2px' }}>{pos.titel ?? '—'} · {pos.ort ?? '—'}</p>
                </div>
                <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                  <span style={{ borderRadius: '9999px', fontSize: '0.6875rem', fontWeight: 500, padding: '2px 8px', background: 'var(--accent-dim)', color: 'var(--accent-light)', border: '1px solid rgba(13,148,136,0.2)', whiteSpace: 'nowrap' }}>
                    {pos.estimated_german_level_needed}+
                  </span>
                  {hasConcern && (
                    <span style={{ borderRadius: '9999px', fontSize: '0.6875rem', fontWeight: 600, padding: '2px 8px', background: 'rgba(239,68,68,0.12)', color: '#F87171', border: '1px solid rgba(239,68,68,0.25)', whiteSpace: 'nowrap' }}>
                      Level concern
                    </span>
                  )}
                </div>
              </div>
              <p style={{ fontSize: '0.8125rem', color: '#9CA3AF', lineHeight: 1.5, marginTop: '8px' }}>{pos.fit_explanation}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                {pos.eintrittsdatum && <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>Start: {pos.eintrittsdatum}</span>}
                {pos.application_url && (
                  <a href={pos.application_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem', color: 'var(--accent-light)' }}>
                    View on BA →
                  </a>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Left panel queue item
function QueueItem({
  row, selected, onClick,
}: { row: DiagnosticRow; selected: boolean; onClick: () => void }) {
  const reviewed = isReviewed(row)
  const score = row.overall_score
  return (
    <button
      onClick={onClick}
      style={{
        display: 'block', width: '100%', textAlign: 'left', padding: '12px 16px',
        border: 'none', cursor: 'pointer',
        background: selected ? 'rgba(13,148,136,0.08)' : 'transparent',
        borderLeft: selected ? '3px solid var(--accent)' : '3px solid transparent',
        opacity: reviewed ? 0.45 : 1,
        transition: 'background 0.15s ease, opacity 0.15s ease',
      }}
      onMouseEnter={(e) => { if (!selected) e.currentTarget.style.background = 'rgba(255,255,255,0.03)' }}
      onMouseLeave={(e) => { if (!selected) e.currentTarget.style.background = 'transparent' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F9FAFB', lineHeight: 1.3, flex: 1 }}>
          {studentDisplayName(row.students)}
        </span>
        {score !== null && score !== undefined && (
          <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: barColor(score), flexShrink: 0 }}>{score}</span>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', flexWrap: 'wrap' }}>
        {row.students?.pathway && <PathwayBadge pathway={row.students.pathway} />}
        <span style={{ fontSize: '0.6875rem', color: '#6B7280' }}>{timeAgo(row.created_at)}</span>
      </div>
      {reviewed && (
        <span style={{
          display: 'inline-block', fontSize: '0.625rem', fontWeight: 600,
          color: row.status === 'approved' ? '#10B981' : '#EF4444',
          textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '4px',
        }}>
          {row.status}
        </span>
      )}
    </button>
  )
}

// Detail panel — right side of the split layout
function DetailPanel({
  row, notes, onNotesChange, onApprove, onReject, onMarkBooked, adminToken,
}: {
  row: DiagnosticRow
  notes: string
  onNotesChange: (v: string) => void
  onApprove: (id: string, notes: string) => Promise<void>
  onReject: (id: string, notes: string) => Promise<void>
  onMarkBooked: (id: string) => Promise<void>
  adminToken: string
}) {
  const [busy, setBusy] = useState(false)
  const [bookingBusy, setBookingBusy] = useState(false)
  const [roadmapOpen, setRoadmapOpen] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Reset roadmap open state when row changes
  useEffect(() => { setRoadmapOpen(true) }, [row.id])

  async function act(fn: (id: string, n: string) => Promise<void>) {
    setBusy(true)
    await fn(row.id, notes)
    setBusy(false)
  }

  const score = row.overall_score

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Scrollable content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>
        {/* Profile header */}
        <div className="glass" style={{ borderRadius: '16px', padding: '20px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          {score !== null && score !== undefined && <ScoreRing score={score} size={72} />}
          <div style={{ flex: 1, minWidth: 0 }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#F9FAFB', letterSpacing: '-0.02em', marginBottom: '4px' }}>
              {studentDisplayName(row.students)}
            </h2>
            {row.students?.email && (
              <p style={{ fontSize: '0.8125rem', color: '#6B7280', marginBottom: '8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {row.students.email}
              </p>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              {row.students?.country && (
                <span style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>
                  {countryFlag(row.students.country)} {row.students.country}
                </span>
              )}
              {row.students?.pathway && <PathwayBadge pathway={row.students.pathway} />}
              {score !== null && score !== undefined && (
                <span style={{ fontSize: '0.75rem', fontWeight: 500, color: scoreColor(score) }}>
                  {scoreLabel(score)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Two-column grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '60% 40%', gap: '20px', alignItems: 'start' }}>
          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {row.summary && (
              <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
                <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>AI Summary</p>
                <p style={{ fontSize: '0.875rem', color: '#9CA3AF', lineHeight: 1.6 }}>{row.summary}</p>
              </div>
            )}

            {row.next_step_message && (
              <div className="glass" style={{ borderRadius: '12px', padding: '16px', borderLeft: '3px solid var(--accent)' }}>
                <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Next Step</p>
                <p style={{ fontSize: '0.875rem', color: '#9CA3AF', lineHeight: 1.6 }}>{row.next_step_message}</p>
              </div>
            )}

            {row.roadmap && row.roadmap.length > 0 && (
              <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
                <button
                  onClick={() => setRoadmapOpen((o) => !o)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: roadmapOpen ? '12px' : 0 }}
                >
                  <span style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    Roadmap ({row.roadmap.length} steps)
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>{roadmapOpen ? '▲' : '▼'}</span>
                </button>

                {roadmapOpen && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {row.roadmap.map((step, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px' }}>
                        <div style={{
                          width: '30px', height: '30px', borderRadius: '9999px',
                          background: 'var(--accent-dim)', color: 'var(--accent-light)',
                          fontSize: '0.6875rem', fontWeight: 700,
                          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                        }}>
                          M{step.month}
                        </div>
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#F9FAFB', marginBottom: '2px' }}>{step.title}</p>
                          <p style={{ fontSize: '0.75rem', color: '#6B7280', lineHeight: 1.5 }}>{step.description}</p>
                          {step.action_items && step.action_items.length > 0 && (
                            <ul style={{ marginTop: '4px', paddingLeft: '14px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              {step.action_items.map((item, j) => (
                                <li key={j} style={{ fontSize: '0.75rem', color: '#9CA3AF' }}>{item}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {row.recommendations && row.recommendations.length > 0 && (
              <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
                <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Recommendations</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {row.recommendations.map((rec, i) => (
                    <div key={i} style={{ borderRadius: '8px', border: '1px solid #1F2937', padding: '10px', background: 'rgba(255,255,255,0.02)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                        <div>
                          <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#F9FAFB' }}>{rec.name}</p>
                          <p style={{ fontSize: '0.75rem', color: '#6B7280', marginTop: '2px' }}>{rec.type}</p>
                        </div>
                        {rec.url && (
                          <a href={rec.url} target="_blank" rel="noopener noreferrer"
                            style={{ fontSize: '0.75rem', color: 'var(--accent-light)', flexShrink: 0 }}>
                            View →
                          </a>
                        )}
                      </div>
                      {rec.description && (
                        <p style={{ fontSize: '0.75rem', color: '#9CA3AF', lineHeight: 1.5, marginTop: '6px' }}>{rec.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {row.students?.pathway === 'ausbildung' && (
              <MatchedPositionsSection diagnosticId={row.id} adminToken={adminToken} />
            )}
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {row.dimension_scores && (
              <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
                <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Dimension Scores</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {DIMENSION_LABELS.map(({ key, label }) => (
                    <ScoreBar key={key} label={label} value={row.dimension_scores![key] ?? 0} />
                  ))}
                </div>
              </div>
            )}

            <div className="glass" style={{ borderRadius: '12px', padding: '16px' }}>
              <label style={{ fontSize: '0.75rem', color: '#6B7280', display: 'block', marginBottom: '8px' }}>
                Reviewer Notes
              </label>
              <textarea
                ref={textareaRef}
                value={notes}
                onChange={(e) => {
                  onNotesChange(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = `${e.target.scrollHeight}px`
                }}
                placeholder="Add review notes (required for rejection)..."
                style={{
                  width: '100%', minHeight: '80px', background: 'rgba(255,255,255,0.04)',
                  border: '1px solid #1F2937', borderRadius: '8px', color: '#F9FAFB',
                  fontSize: '0.875rem', padding: '10px', resize: 'none', overflow: 'hidden', outline: 'none',
                }}
                onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
                onBlur={(e) => (e.target.style.borderColor = '#1F2937')}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Sticky action bar */}
      <div style={{ flexShrink: 0, padding: '16px 28px', borderTop: '1px solid #1F2937', background: '#111827' }}>
        {row.status === 'approved' ? (
          row.consultation_booked ? (
            <div style={{
              borderRadius: '12px', border: '1px solid rgba(13,148,136,0.3)',
              background: 'rgba(13,148,136,0.08)', color: '#2DD4BF',
              fontSize: '0.875rem', fontWeight: 600, padding: '14px', textAlign: 'center',
            }}>
              <CheckCircle2 size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
              Booked ✓
            </div>
          ) : (
            <button
              onClick={async () => { setBookingBusy(true); await onMarkBooked(row.id); setBookingBusy(false) }}
              disabled={bookingBusy}
              style={{
                background: 'rgba(13,148,136,0.12)', border: '1px solid rgba(13,148,136,0.35)',
                borderRadius: '12px', color: '#2DD4BF', fontSize: '0.9375rem', fontWeight: 600,
                padding: '14px', width: '100%', cursor: bookingBusy ? 'not-allowed' : 'pointer',
                opacity: bookingBusy ? 0.5 : 1, minHeight: '48px', transition: 'filter 0.15s ease',
              }}
              onMouseEnter={(e) => { if (!bookingBusy) e.currentTarget.style.filter = 'brightness(1.12)' }}
              onMouseLeave={(e) => { if (!bookingBusy) e.currentTarget.style.filter = 'brightness(1)' }}
            >
              ✓ Mark as Booked
            </button>
          )
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <button
              onClick={() => act(onReject)} disabled={busy}
              style={{
                background: 'transparent', border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: '12px', color: '#EF4444', fontSize: '0.9375rem', fontWeight: 500,
                padding: '14px', cursor: busy ? 'not-allowed' : 'pointer', opacity: busy ? 0.5 : 1,
                minHeight: '48px', transition: 'background 0.15s ease', width: '100%',
              }}
              onMouseEnter={(e) => { if (!busy) e.currentTarget.style.background = 'rgba(239,68,68,0.1)' }}
              onMouseLeave={(e) => { if (!busy) e.currentTarget.style.background = 'transparent' }}
            >
              ✕ Reject
            </button>
            <button
              onClick={() => act(onApprove)} disabled={busy}
              style={{
                background: 'var(--accent)', border: 'none', borderRadius: '12px',
                color: 'white', fontSize: '0.9375rem', fontWeight: 600,
                padding: '14px', cursor: busy ? 'not-allowed' : 'pointer', opacity: busy ? 0.5 : 1,
                minHeight: '48px', transition: 'background 0.15s ease', width: '100%',
              }}
              onMouseEnter={(e) => { if (!busy) e.currentTarget.style.background = 'var(--accent-light)' }}
              onMouseLeave={(e) => { if (!busy) e.currentTarget.style.background = 'var(--accent)' }}
            >
              ✓ Approve
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Legacy drawer for narrow screens — keeps original UX on mobile
function DetailsPanel({
  row, notes, onNotesChange, onClose, onApprove, onReject, onMarkBooked, adminToken,
}: {
  row: DiagnosticRow; notes: string; onNotesChange: (v: string) => void; onClose: () => void
  onApprove: (id: string, notes: string) => Promise<void>
  onReject: (id: string, notes: string) => Promise<void>
  onMarkBooked: (id: string) => Promise<void>; adminToken: string
}) {
  const [busy, setBusy] = useState(false)
  const [bookingBusy, setBookingBusy] = useState(false)
  const [roadmapOpen, setRoadmapOpen] = useState(false)

  async function act(fn: (id: string, n: string) => Promise<void>) {
    setBusy(true); await fn(row.id, notes); setBusy(false)
  }

  const score = row.overall_score
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} />
      <div onClick={(e) => e.stopPropagation()} style={{
        position: 'fixed', right: 0, top: 0, bottom: 0, zIndex: 50,
        width: 'min(520px, 100vw)', background: '#111827', borderLeft: '1px solid #1F2937',
        overflowY: 'auto', padding: '24px', animation: 'slideInPanel 0.3s ease forwards',
      }}>
        <button onClick={onClose} className="glass" style={{
          position: 'absolute', top: '16px', right: '16px', width: '32px', height: '32px',
          borderRadius: '9999px', border: 'none', color: '#F9FAFB', fontSize: '18px', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1,
        }}>×</button>

        <div style={{ marginTop: '8px' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#F9FAFB', letterSpacing: '-0.02em' }}>
            {studentDisplayName(row.students)}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>{row.students?.email}</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
            <Globe size={14} color="#9CA3AF" />
            <span style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>{row.students?.country}</span>
            {row.students?.pathway && <PathwayBadge pathway={row.students.pathway} />}
          </div>
        </div>

        {score !== null && score !== undefined && (
          <div className="glass" style={{ borderRadius: '16px', padding: '20px', marginTop: '24px' }}>
            <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Overall Score</p>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
              <span className="gradient-text" style={{ fontSize: '3rem', fontWeight: 700, lineHeight: 1 }}>{score}</span>
              <span style={{ fontSize: '1.25rem', color: '#9CA3AF', marginBottom: '4px' }}>/100</span>
            </div>
            {row.dimension_scores && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
                {DIMENSION_LABELS.map(({ key, label }) => {
                  const val = row.dimension_scores![key] ?? 0
                  return (
                    <div key={key}>
                      <p style={{ fontSize: '0.75rem', color: '#6B7280', marginBottom: '4px' }}>{label}</p>
                      <p style={{ fontSize: '1.125rem', fontWeight: 700, color: scoreColor(val) }}>{val}</p>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {row.summary && (
          <div className="glass" style={{ borderRadius: '16px', padding: '20px', marginTop: '16px' }}>
            <p style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>AI Summary</p>
            <p style={{ fontSize: '0.875rem', color: '#9CA3AF', lineHeight: 1.6 }}>{row.summary}</p>
          </div>
        )}

        <div style={{ marginTop: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', color: '#9CA3AF', marginBottom: '8px' }}>Reviewer notes (optional)</label>
          <textarea rows={3} value={notes} onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Add any notes for this student..."
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid #1F2937', borderRadius: '12px', color: '#F9FAFB', fontSize: '0.875rem', outline: 'none', padding: '12px', resize: 'none', width: '100%' }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
            onBlur={(e) => (e.target.style.borderColor = '#1F2937')} />
        </div>

        {row.status === 'approved' ? (
          <div style={{ marginTop: '24px' }}>
            {row.consultation_booked ? (
              <div style={{ borderRadius: '12px', border: '1px solid rgba(13,148,136,0.3)', background: 'rgba(13,148,136,0.08)', color: '#2DD4BF', fontSize: '0.875rem', fontWeight: 600, padding: '12px', textAlign: 'center' }}>
                <CheckCircle2 size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />Booked ✓
              </div>
            ) : (
              <button onClick={async () => { setBookingBusy(true); await onMarkBooked(row.id); setBookingBusy(false) }} disabled={bookingBusy}
                style={{ background: 'rgba(13,148,136,0.12)', border: '1px solid rgba(13,148,136,0.35)', borderRadius: '12px', color: '#2DD4BF', fontSize: '0.875rem', fontWeight: 600, padding: '12px', width: '100%', cursor: bookingBusy ? 'not-allowed' : 'pointer', opacity: bookingBusy ? 0.5 : 1, minHeight: '44px' }}>
                ✓ Mark as Booked
              </button>
            )}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '24px' }}>
            <button onClick={() => act(onReject)} disabled={busy}
              style={{ background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '12px', color: '#EF4444', fontSize: '0.875rem', fontWeight: 500, padding: '12px', cursor: busy ? 'not-allowed' : 'pointer', opacity: busy ? 0.5 : 1, minHeight: '44px' }}
              onMouseEnter={(e) => { if (!busy) e.currentTarget.style.background = 'rgba(239,68,68,0.1)' }}
              onMouseLeave={(e) => { if (!busy) e.currentTarget.style.background = 'transparent' }}>
              ✕ Reject
            </button>
            <button onClick={() => act(onApprove)} disabled={busy}
              style={{ background: 'var(--accent)', border: 'none', borderRadius: '12px', color: 'white', fontSize: '0.875rem', fontWeight: 600, padding: '12px', cursor: busy ? 'not-allowed' : 'pointer', opacity: busy ? 0.5 : 1, minHeight: '44px' }}
              onMouseEnter={(e) => { if (!busy) e.currentTarget.style.background = 'var(--accent-light)' }}
              onMouseLeave={(e) => { if (!busy) e.currentTarget.style.background = 'var(--accent)' }}>
              ✓ Approve
            </button>
          </div>
        )}

        {row.students?.pathway === 'ausbildung' && (
          <MatchedPositionsSection diagnosticId={row.id} adminToken={adminToken} />
        )}

        {row.roadmap && row.roadmap.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <button onClick={() => setRoadmapOpen((o) => !o)} className="glass"
              style={{ borderRadius: '12px', padding: '16px', width: '100%', textAlign: 'left', cursor: 'pointer', border: 'none' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 500, color: '#9CA3AF' }}>
                {roadmapOpen ? '▲' : '▼'} View roadmap ({row.roadmap.length} steps)
              </span>
            </button>
            {roadmapOpen && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                {row.roadmap.slice(0, 3).map((step, i) => (
                  <div key={i} className="glass" style={{ borderRadius: '12px', padding: '16px', display: 'flex', gap: '12px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '9999px', background: 'var(--accent-dim)', color: 'var(--accent-light)', fontSize: '0.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      M{step.month}
                    </div>
                    <div>
                      <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#F9FAFB', marginBottom: '4px' }}>{step.title}</p>
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

// Narrow-screen single-column layout (original layout)
function NarrowAdminLayout({
  rows, filteredRows, loadingRows, selected, setSelected, notes, setNotes,
  stats, tco, latestExperiment, activeFilter, setActiveFilter,
  handleReview, handleMarkBooked, clearAdminSession, adminToken,
  greeting, dateStr,
}: {
  rows: DiagnosticRow[]; filteredRows: DiagnosticRow[]; loadingRows: boolean
  selected: DiagnosticRow | null; setSelected: (r: DiagnosticRow | null) => void
  notes: Record<string, string>; setNotes: React.Dispatch<React.SetStateAction<Record<string, string>>>
  stats: { pending: number; approved_today: number; total: number; approved_count: number; booked_count: number; conversion_rate: number }
  tco: TcoStats | null; latestExperiment: EvaluationExperimentSummary | null
  activeFilter: string; setActiveFilter: (f: string) => void
  handleReview: (id: string, status: 'approved' | 'rejected', notes: string) => Promise<void>
  handleMarkBooked: (id: string) => Promise<void>
  clearAdminSession: () => void; adminToken: string
  greeting: string; dateStr: string
}) {
  const filters = [
    { key: 'all', label: 'All' }, { key: 'ausbildung', label: 'Ausbildung' },
    { key: 'university', label: 'University' }, { key: 'work_visa', label: 'Work Visa' },
  ]
  return (
    <div style={{ background: '#0A0E1A', minHeight: '100vh' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 16px 48px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#F9FAFB', letterSpacing: '-0.02em' }}>{greeting}, Cleo 👋</h1>
            <p style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>{dateStr}</p>
          </div>
          <button onClick={clearAdminSession} className="glass" style={{ borderRadius: '9999px', padding: '8px 16px', fontSize: '0.875rem', color: '#6B7280', cursor: 'pointer', minHeight: '44px', border: 'none' }}>
            Sign out
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
          {[
            { icon: <Inbox size={20} color="var(--accent-light)" />, value: String(stats.pending), label: 'Pending review' },
            { icon: <CheckCircle2 size={20} color="var(--accent-light)" />, value: String(stats.approved_today), label: 'Approved today' },
            { icon: <Gauge size={20} color="var(--accent-light)" />, value: String(stats.total), label: 'All time' },
            { icon: <Gauge size={20} color="var(--accent-light)" />, value: `${stats.conversion_rate}%`, label: 'Conversion rate' },
          ].map((s, i) => (
            <div key={i} className="glass" style={{ borderRadius: '16px', padding: '20px' }}>
              <div style={{ marginBottom: '8px' }}>{s.icon}</div>
              <div className="gradient-text" style={{ fontSize: '1.875rem', fontWeight: 700 }}>{loadingRows ? '—' : s.value}</div>
              <div style={{ fontSize: '0.875rem', color: '#6B7280', marginTop: '4px' }}>{s.label}</div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
          {filters.map((f) => (
            <button key={f.key} onClick={() => setActiveFilter(f.key)} style={{
              borderRadius: '9999px', padding: '6px 16px', fontSize: '0.875rem', cursor: 'pointer', minHeight: '36px',
              background: activeFilter === f.key ? 'var(--accent)' : 'rgba(255,255,255,0.04)',
              color: activeFilter === f.key ? 'white' : '#9CA3AF',
              border: activeFilter === f.key ? 'none' : '1px solid rgba(255,255,255,0.08)',
            }}>{f.label}</button>
          ))}
        </div>

        {loadingRows ? (
          <div className="glass" style={{ borderRadius: '16px', padding: '48px', textAlign: 'center', color: '#6B7280' }}>Loading...</div>
        ) : filteredRows.length === 0 ? (
          <div className="glass" style={{ borderRadius: '16px', padding: '64px 32px', textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>🎉</div>
            <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#F9FAFB', marginBottom: '8px' }}>All caught up!</p>
            <p style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>No diagnostics pending review.</p>
          </div>
        ) : (
          <div>
            {filteredRows.map((row) => (
              <div key={row.id} className="glass" style={{ borderRadius: '16px', padding: '20px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <p style={{ fontSize: '1.125rem', fontWeight: 600, color: '#F9FAFB' }}>{studentDisplayName(row.students)}</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                      <Globe size={14} color="#9CA3AF" />
                      <span style={{ fontSize: '0.875rem', color: '#9CA3AF' }}>{row.students?.country}</span>
                      {row.students?.pathway && <PathwayBadge pathway={row.students.pathway} />}
                    </div>
                  </div>
                  <span className="glass" style={{ borderRadius: '9999px', padding: '4px 12px', fontSize: '0.75rem', color: '#6B7280', whiteSpace: 'nowrap', flexShrink: 0 }}>
                    {timeAgo(row.created_at)}
                  </span>
                </div>
                {row.overall_score !== null && row.overall_score !== undefined && (
                  <div style={{ marginTop: '12px' }}>
                    <div style={{ height: '6px', background: '#1F2937', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${row.overall_score}%`, background: scoreColor(row.overall_score), borderRadius: '9999px' }} />
                    </div>
                    <span style={{ fontSize: '0.75rem', color: '#6B7280', marginTop: '4px', display: 'block' }}>Score: {row.overall_score}/100</span>
                  </div>
                )}
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button onClick={() => setSelected(row)} className="glass" style={{ borderRadius: '9999px', padding: '8px 16px', fontSize: '0.875rem', color: '#9CA3AF', cursor: 'pointer', minHeight: '44px', border: 'none' }}>
                    View details
                  </button>
                  <button onClick={() => handleReview(row.id, 'rejected', notes[row.id] ?? '')}
                    style={{ background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '9999px', color: '#EF4444', fontSize: '0.875rem', padding: '8px 16px', cursor: 'pointer', minHeight: '44px' }}>
                    ✕ Reject
                  </button>
                  <button onClick={() => handleReview(row.id, 'approved', notes[row.id] ?? '')}
                    style={{ background: 'var(--accent)', border: 'none', borderRadius: '9999px', color: 'white', fontSize: '0.875rem', fontWeight: 600, padding: '8px 20px', cursor: 'pointer', minHeight: '44px' }}>
                    ✓ Approve
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <DetailsPanel
          row={selected} notes={notes[selected.id] ?? ''}
          onNotesChange={(v) => setNotes((prev) => ({ ...prev, [selected.id]: v }))}
          onClose={() => setSelected(null)}
          onApprove={(id, n) => handleReview(id, 'approved', n)}
          onReject={(id, n) => handleReview(id, 'rejected', n)}
          onMarkBooked={handleMarkBooked} adminToken={adminToken}
        />
      )}
    </div>
  )
}

export default function AdminPage() {
  const [authed, setAuthed] = useState(false)
  const [adminToken, setAdminToken] = useState<string | null>(null)
  const [rows, setRows] = useState<DiagnosticRow[]>([])
  const [loadingRows, setLoadingRows] = useState(false)
  const [selected, setSelected] = useState<DiagnosticRow | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [activeFilter, setActiveFilter] = useState('all')
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [stats, setStats] = useState({ pending: 0, approved_today: 0, total: 0, approved_count: 0, booked_count: 0, conversion_rate: 0 })
  const [tco, setTco] = useState<TcoStats | null>(null)
  const [latestExperiment, setLatestExperiment] = useState<EvaluationExperimentSummary | null>(null)
  const [tcoOpen, setTcoOpen] = useState(false)
  const isWide = useIsWide()

  const clearAdminSession = useCallback(() => {
    sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY)
    setAdminToken(null); setAuthed(false); setRows([]); setSelected(null); setTco(null); setLatestExperiment(null)
  }, [])

  const adminHeaders = useCallback(
    (extra?: Record<string, string>) => ({ ...(extra ?? {}), Authorization: `Bearer ${adminToken}` }),
    [adminToken]
  )

  useEffect(() => {
    const storedToken = sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY)
    if (storedToken) { setAdminToken(storedToken); setAuthed(true) }
  }, [])

  async function handleAdminLogin(token: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_URL}/api/admin/stats`, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) return false
      const data = await res.json()
      sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token)
      setAdminToken(token); setAuthed(true); setStats(data)
      return true
    } catch { return false }
  }

  const fetchRows = useCallback(async () => {
    if (!adminToken) return
    setLoadingRows(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/diagnostics`, { headers: adminHeaders() })
      if (isAuthFailure(res.status)) { clearAdminSession(); return }
      if (!res.ok) throw new Error()
      setRows(await res.json())
    } catch { /* silently fail */ } finally { setLoadingRows(false) }
  }, [adminHeaders, adminToken, clearAdminSession])

  const fetchStats = useCallback(async () => {
    if (!adminToken) return
    try {
      const res = await fetch(`${API_URL}/api/admin/stats`, { headers: adminHeaders() })
      if (isAuthFailure(res.status)) { clearAdminSession(); return }
      if (res.ok) setStats(await res.json())
    } catch { /* silently fail */ }
  }, [adminHeaders, adminToken, clearAdminSession])

  const fetchTco = useCallback(async () => {
    if (!adminToken) return
    try {
      const res = await fetch(`${API_URL}/api/admin/tco`, { headers: adminHeaders() })
      if (isAuthFailure(res.status)) { clearAdminSession(); return }
      if (res.ok) setTco(await res.json())
    } catch { /* silently fail */ }
  }, [adminHeaders, adminToken, clearAdminSession])

  const fetchEvaluationSummary = useCallback(async () => {
    if (!adminToken) return
    try {
      const res = await fetch(`${API_URL}/api/admin/evaluation/summary`, { headers: adminHeaders() })
      if (isAuthFailure(res.status)) { clearAdminSession(); return }
      if (res.ok) { const data = await res.json(); setLatestExperiment(data.latest_experiment ?? null) }
    } catch { /* silently fail */ }
  }, [adminHeaders, adminToken, clearAdminSession])

  useEffect(() => {
    if (authed && adminToken) { fetchRows(); fetchStats(); fetchTco(); fetchEvaluationSummary() }
  }, [adminToken, authed, fetchRows, fetchStats, fetchTco, fetchEvaluationSummary])

  const filteredRows = activeFilter === 'all' ? rows : rows.filter((r) => r.students?.pathway === activeFilter)

  async function handleReview(id: string, status: 'approved' | 'rejected', reviewerNotes: string) {
    if (!adminToken) return
    try {
      const res = await fetch(`${API_URL}/api/admin/diagnostics/${id}/review`, {
        method: 'POST',
        headers: adminHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ status, reviewer_notes: reviewerNotes }),
      })
      if (isAuthFailure(res.status)) { clearAdminSession(); return }
      if (!res.ok) {
        setToast({ message: `Failed to ${status} — server returned ${res.status}. Try again.`, type: 'error' })
        return
      }

      // Find next pending before updating state
      const allPending = filteredRows.filter((r) => !isReviewed(r))
      const idx = allPending.findIndex((r) => r.id === id)
      const nextPending = allPending[idx + 1] ?? allPending[idx - 1] ?? null

      setRows((prev) => prev.map((r) => r.id === id ? { ...r, status } : r))
      setSelected(nextPending)
      setToast(status === 'approved'
        ? { message: '✓ Approved — student will be notified', type: 'success' }
        : { message: '✕ Rejected', type: 'error' }
      )
      fetchStats()
    } catch {
      setToast({ message: 'Network error — check your connection and try again.', type: 'error' })
    }
  }

  async function handleMarkBooked(id: string) {
    if (!adminToken) return
    try {
      const res = await fetch(`${API_URL}/api/admin/diagnostics/${id}/mark-booked`, { method: 'POST', headers: adminHeaders() })
      if (isAuthFailure(res.status)) { clearAdminSession(); return }
      if (!res.ok) {
        setToast({ message: `Failed to record booking — server returned ${res.status}.`, type: 'error' })
        return
      }
      setRows((prev) => prev.map((r) => r.id === id ? { ...r, consultation_booked: true } : r))
      setSelected((prev) => prev?.id === id ? { ...prev, consultation_booked: true } : prev)
      setToast({ message: 'Booking recorded — conversion tracked', type: 'success' })
      fetchStats()
    } catch {
      setToast({ message: 'Network error — check your connection and try again.', type: 'error' })
    }
  }

  // Keyboard navigation
  useEffect(() => {
    if (!isWide) return
    function handleKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return
      const pending = filteredRows.filter((r) => !isReviewed(r))
      const idx = selected ? pending.findIndex((r) => r.id === selected.id) : -1
      if (e.key === 'ArrowRight' || e.key === 'k') {
        if (idx < pending.length - 1) setSelected(pending[idx + 1])
        else if (idx === -1 && pending.length > 0) setSelected(pending[0])
      }
      if (e.key === 'ArrowLeft' || e.key === 'j') {
        if (idx > 0) setSelected(pending[idx - 1])
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [selected, filteredRows, isWide])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const dateStr = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

  if (!authed || !adminToken) return <PasswordScreen onLogin={handleAdminLogin} />

  if (!isWide) {
    return (
      <>
        <NarrowAdminLayout
          rows={rows} filteredRows={filteredRows} loadingRows={loadingRows}
          selected={selected} setSelected={setSelected} notes={notes} setNotes={setNotes}
          stats={stats} tco={tco} latestExperiment={latestExperiment}
          activeFilter={activeFilter} setActiveFilter={setActiveFilter}
          handleReview={handleReview} handleMarkBooked={handleMarkBooked}
          clearAdminSession={clearAdminSession} adminToken={adminToken}
          greeting={greeting} dateStr={dateStr}
        />
        {toast && <Toast message={toast.message} type={toast.type} onDone={() => setToast(null)} />}
      </>
    )
  }

  // Wide layout — two-panel master-detail
  const filters = [
    { key: 'all', label: 'All' }, { key: 'ausbildung', label: 'Ausbildung' },
    { key: 'university', label: 'University' }, { key: 'work_visa', label: 'Work Visa' },
  ]
  const pendingRows = filteredRows.filter((r) => !isReviewed(r))
  const reviewedRows = filteredRows.filter((r) => isReviewed(r))
  const pendingCount = rows.filter((r) => !isReviewed(r)).length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', background: '#0A0E1A' }}>
      {/* Top bar */}
      <div style={{
        flexShrink: 0, display: 'flex', alignItems: 'center', gap: '16px',
        padding: '12px 24px', borderBottom: '1px solid #1F2937', background: '#0A0E1A',
        flexWrap: 'wrap',
      }}>
        <div style={{ marginRight: 'auto' }}>
          <span style={{ fontSize: '1rem', fontWeight: 700, color: '#F9FAFB' }}>{greeting}, Cleo 👋</span>
          <span style={{ fontSize: '0.8125rem', color: '#6B7280', marginLeft: '12px' }}>{dateStr}</span>
        </div>
        {/* Inline stats */}
        {[
          { icon: <Inbox size={14} color="var(--accent-light)" />, value: loadingRows ? '—' : String(stats.pending), label: 'pending' },
          { icon: <CheckCircle2 size={14} color="var(--accent-light)" />, value: loadingRows ? '—' : String(stats.approved_today), label: 'approved today' },
          { icon: <Gauge size={14} color="var(--accent-light)" />, value: loadingRows ? '—' : `${stats.conversion_rate}%`, label: 'conversion' },
        ].map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '9999px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
            {s.icon}
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#F9FAFB' }}>{s.value}</span>
            <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>{s.label}</span>
          </div>
        ))}
        <button onClick={clearAdminSession} className="glass" style={{ borderRadius: '9999px', padding: '6px 14px', fontSize: '0.8125rem', color: '#6B7280', cursor: 'pointer', minHeight: '36px', border: 'none' }}>
          Sign out
        </button>
      </div>

      {/* Two-panel layout */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left panel — queue */}
        <div style={{
          width: '280px', flexShrink: 0, borderRight: '1px solid #1F2937',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}>
          {/* Sticky header */}
          <div style={{
            flexShrink: 0, padding: '16px', borderBottom: '1px solid #1F2937',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: '#0A0E1A',
          }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#F9FAFB' }}>Review Queue</span>
            {pendingCount > 0 && (
              <span style={{
                background: 'var(--accent)', color: 'white', borderRadius: '9999px',
                fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', minWidth: '24px', textAlign: 'center',
              }}>
                {pendingCount}
              </span>
            )}
          </div>

          {/* Filter chips */}
          <div style={{ flexShrink: 0, padding: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap', borderBottom: '1px solid #1F2937' }}>
            {filters.map((f) => (
              <button key={f.key} onClick={() => setActiveFilter(f.key)} style={{
                borderRadius: '9999px', padding: '4px 10px', fontSize: '0.75rem', cursor: 'pointer',
                background: activeFilter === f.key ? 'var(--accent)' : 'rgba(255,255,255,0.04)',
                color: activeFilter === f.key ? 'white' : '#9CA3AF',
                border: activeFilter === f.key ? 'none' : '1px solid rgba(255,255,255,0.08)',
              }}>
                {f.label}
              </button>
            ))}
          </div>

          {/* Scrollable list */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {loadingRows ? (
              <div style={{ padding: '24px', textAlign: 'center', color: '#6B7280', fontSize: '0.875rem' }}>Loading…</div>
            ) : pendingRows.length === 0 && reviewedRows.length === 0 ? (
              <div style={{ padding: '32px 16px', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🎉</div>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F9FAFB' }}>All caught up!</p>
                <p style={{ fontSize: '0.75rem', color: '#6B7280', marginTop: '4px' }}>No diagnostics pending.</p>
              </div>
            ) : (
              <>
                {pendingRows.map((row) => (
                  <QueueItem key={row.id} row={row} selected={selected?.id === row.id} onClick={() => setSelected(row)} />
                ))}

                {reviewedRows.length > 0 && (
                  <>
                    <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '1px', background: '#1F2937' }} />
                      <span style={{ fontSize: '0.625rem', color: '#4B5563', textTransform: 'uppercase', letterSpacing: '0.08em', whiteSpace: 'nowrap' }}>reviewed</span>
                      <div style={{ flex: 1, height: '1px', background: '#1F2937' }} />
                    </div>
                    {reviewedRows.map((row) => (
                      <QueueItem key={row.id} row={row} selected={selected?.id === row.id} onClick={() => setSelected(row)} />
                    ))}
                  </>
                )}

                {/* TCO & eval accordion at bottom */}
                <div style={{ borderTop: '1px solid #1F2937', marginTop: '8px' }}>
                  <button
                    onClick={() => setTcoOpen((o) => !o)}
                    style={{
                      width: '100%', textAlign: 'left', padding: '12px 16px', background: 'none',
                      border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    }}
                  >
                    <span style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.08em' }}>AI Stats</span>
                    <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>{tcoOpen ? '▲' : '▼'}</span>
                  </button>

                  {tcoOpen && tco && (
                    <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {[
                        { label: 'AI cost', value: formatUsd(tco.estimated_cost) },
                        { label: 'Forecast', value: formatUsd(tco.forecasted_month_end_cost) },
                        { label: 'Calls', value: String(tco.current_month_ai_calls) },
                        { label: 'Failures', value: String(tco.failed_calls) },
                        { label: 'Avg cost', value: formatUsd(tco.average_cost_per_diagnostic) },
                        { label: 'Avg latency', value: `${Math.round(tco.average_latency_ms)}ms` },
                      ].map((item) => (
                        <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.75rem', color: '#6B7280' }}>{item.label}</span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#F9FAFB' }}>{item.value}</span>
                        </div>
                      ))}

                      {latestExperiment && (
                        <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #1F2937' }}>
                          <p style={{ fontSize: '0.75rem', color: '#6B7280', marginBottom: '6px' }}>
                            Experiment: <span style={{ color: '#9CA3AF' }}>{latestExperiment.name}</span>
                          </p>
                          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.6875rem', color: '#2DD4BF' }}>p={formatStat(latestExperiment.latest_comparison?.p_value ?? latestExperiment.summary?.p_value, 4)}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#9CA3AF' }}>effect={formatStat(latestExperiment.latest_comparison?.effect_size ?? latestExperiment.summary?.effect_size)}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right panel — detail or empty state */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {selected ? (
            <DetailPanel
              row={selected}
              notes={notes[selected.id] ?? ''}
              onNotesChange={(v) => setNotes((prev) => ({ ...prev, [selected.id]: v }))}
              onApprove={(id, n) => handleReview(id, 'approved', n)}
              onReject={(id, n) => handleReview(id, 'rejected', n)}
              onMarkBooked={handleMarkBooked}
              adminToken={adminToken}
            />
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', color: '#6B7280' }}>
              <div style={{ fontSize: '2rem' }}>📋</div>
              <p style={{ fontSize: '1rem', fontWeight: 600, color: '#9CA3AF' }}>Select a diagnostic to review</p>
              <p style={{ fontSize: '0.875rem', color: '#6B7280' }}>
                {pendingCount > 0
                  ? `${pendingCount} pending · use ← → or J/K to navigate`
                  : 'No pending diagnostics'}
              </p>
            </div>
          )}
        </div>
      </div>

      {toast && <Toast message={toast.message} type={toast.type} onDone={() => setToast(null)} />}
    </div>
  )
}
