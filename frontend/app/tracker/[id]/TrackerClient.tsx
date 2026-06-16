'use client'
import { useEffect, useState } from 'react'

interface RoadmapStep {
  month: number
  title: string
  description: string
  action_items: string[]
}

interface TrackerClientProps {
  diagnosticId: string
  studentName: string
  roadmap: RoadmapStep[]
  initialCompleted: number[]
  apiUrl: string
}

export default function TrackerClient({
  diagnosticId,
  studentName,
  roadmap,
  initialCompleted,
  apiUrl,
}: TrackerClientProps) {
  const [completed, setCompleted] = useState<number[]>(initialCompleted)
  const [saving, setSaving] = useState(false)
  const [progressToken, setProgressToken] = useState<string | null>(null)
  const [authError, setAuthError] = useState(false)

  useEffect(() => {
    setProgressToken(sessionStorage.getItem(`klar_progress_token_${diagnosticId}`))
  }, [diagnosticId])

  const progressPct = roadmap.length > 0
    ? Math.round((completed.length / roadmap.length) * 100)
    : 0

  const toggleStep = async (month: number) => {
    const updated = completed.includes(month)
      ? completed.filter((m) => m !== month)
      : [...completed, month]

    const previous = completed
    setCompleted(updated)
    setSaving(true)

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (progressToken) {
        headers.Authorization = `Bearer ${progressToken}`
      }
      const res = await fetch(`${apiUrl}/api/diagnostic/${diagnosticId}/progress`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ completed_steps: updated }),
      })
      if (res.status === 401) {
        setCompleted(previous)
        setAuthError(true)
        return
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    } catch (err) {
      console.error('Failed to save progress:', err)
      setCompleted(previous)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0A0E1A', padding: '24px' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto', paddingTop: '48px' }}>

        {/* Back link */}
        <a
          href={`/results/${diagnosticId}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            color: '#6B7280',
            fontSize: '14px',
            textDecoration: 'none',
            marginBottom: '32px',
          }}
        >
          ← Back to results
        </a>

        <h1 style={{
          fontSize: '32px',
          fontWeight: 700,
          color: '#F9FAFB',
          letterSpacing: '-0.02em',
          marginBottom: '8px',
        }}>
          {studentName}&apos;s Progress Tracker
        </h1>
        <p style={{ color: '#9CA3AF', marginBottom: '32px' }}>
          Check off each step as you complete it.
        </p>

        {/* Progress card */}
        <div style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '32px',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '12px',
          }}>
            <span style={{ color: '#F9FAFB', fontWeight: 600 }}>
              Overall Progress
            </span>
            <span style={{
              color: progressPct === 100 ? '#0D9488' : '#3B82F6',
              fontWeight: 700,
            }}>
              {progressPct}%
            </span>
          </div>
          <div style={{
            height: '10px',
            background: '#1F2937',
            borderRadius: '9999px',
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${progressPct}%`,
              background: progressPct === 100
                ? 'linear-gradient(90deg, #0D9488, #14B8A6)'
                : 'linear-gradient(90deg, #3B82F6, #8B5CF6)',
              borderRadius: '9999px',
              transition: 'width 0.4s ease',
            }} />
          </div>
          <p style={{ color: '#6B7280', fontSize: '13px', marginTop: '10px' }}>
            {completed.length} of {roadmap.length} steps completed
            {progressPct === 100 && ' — 🎉 You completed your roadmap!'}
          </p>
        </div>

        {/* Step cards */}
        {roadmap.map((step) => {
          const isDone = completed.includes(step.month)
          return (
            <div
              key={step.month}
              onClick={() => toggleStep(step.month)}
              style={{
                background: isDone ? 'rgba(13,148,136,0.08)' : 'rgba(255,255,255,0.04)',
                border: isDone
                  ? '1px solid rgba(13,148,136,0.3)'
                  : '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px',
                padding: '20px',
                marginBottom: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                gap: '16px',
                alignItems: 'flex-start',
              }}
              onMouseEnter={(e) => {
                if (!isDone) {
                  e.currentTarget.style.borderColor = 'rgba(59,130,246,0.4)'
                  e.currentTarget.style.background = 'rgba(59,130,246,0.06)'
                }
              }}
              onMouseLeave={(e) => {
                if (!isDone) {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)'
                }
              }}
            >
              {/* Checkbox circle */}
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                border: isDone ? 'none' : '2px solid #374151',
                background: isDone ? '#0D9488' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '2px',
                color: 'white',
                fontSize: '14px',
                fontWeight: 700,
                transition: 'all 0.2s',
              }}>
                {isDone ? '✓' : step.month}
              </div>

              {/* Content */}
              <div style={{ flex: 1 }}>
                <p style={{
                  fontSize: '12px',
                  color: '#6B7280',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '4px',
                }}>
                  Month {step.month}
                </p>
                <h3 style={{
                  fontSize: '17px',
                  fontWeight: 600,
                  color: isDone ? '#6B7280' : '#F9FAFB',
                  textDecoration: isDone ? 'line-through' : 'none',
                  marginBottom: '6px',
                  transition: 'all 0.2s',
                }}>
                  {step.title}
                </h3>
                <p style={{ fontSize: '14px', color: '#9CA3AF', lineHeight: 1.6 }}>
                  {step.description}
                </p>
                {!isDone && step.action_items && step.action_items.length > 0 && (
                  <ul style={{ marginTop: '10px', paddingLeft: 0, listStyle: 'none' }}>
                    {step.action_items.map((item, j) => (
                      <li
                        key={j}
                        style={{
                          display: 'flex',
                          gap: '8px',
                          alignItems: 'flex-start',
                          fontSize: '13px',
                          color: '#6B7280',
                          marginBottom: '4px',
                        }}
                      >
                        <span style={{
                          width: '5px',
                          height: '5px',
                          borderRadius: '50%',
                          background: '#3B82F6',
                          marginTop: '6px',
                          flexShrink: 0,
                        }} />
                        {item}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )
        })}

        {saving && (
          <p style={{
            textAlign: 'center',
            color: '#6B7280',
            fontSize: '12px',
            marginTop: '16px',
          }}>
            Saving...
          </p>
        )}

        {authError && (
          <div style={{
            marginTop: '24px',
            padding: '16px',
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.25)',
            borderRadius: '12px',
            color: '#FCA5A5',
            fontSize: '14px',
            lineHeight: 1.6,
          }}>
            This tracker can only be updated from the browser where you originally submitted your diagnostic. If you&apos;re on a different device, please contact your consultant to sync your progress.
          </div>
        )}
      </div>
    </div>
  )
}
