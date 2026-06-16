import MatchesClient from './MatchesClient'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const FETCH_TIMEOUT_MS = 8000

async function fetchJson<T>(url: string): Promise<T | null> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const res = await fetch(url, { cache: 'no-store', signal: controller.signal })
    if (!res.ok) return null
    return await res.json() as T
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

type DiagnosticResult = { status: string; students?: { name?: string | null } | null }
type MatchesResult = {
  matched_positions: {
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
  }[]
  reasoning_summary: string | null
  status: string
}

export default async function MatchesPage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params

  const [diagnostic, matches] = await Promise.all([
    fetchJson<DiagnosticResult>(`${API_URL}/api/diagnostic/${id}/result`),
    fetchJson<MatchesResult>(`${API_URL}/api/diagnostic/${id}/matches`),
  ])

  if (!diagnostic || diagnostic.status !== 'approved') {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#0A0E1A',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        textAlign: 'center',
        padding: '24px',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
        <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#F9FAFB', margin: 0 }}>
          Positions not yet available
        </h2>
        <p style={{ color: '#9CA3AF', marginTop: '12px', maxWidth: '400px', lineHeight: 1.6 }}>
          Matched positions are only available once your diagnostic has been approved.
        </p>
        <a href={`/results/${id}`} style={{
          marginTop: '32px',
          background: 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#F9FAFB',
          padding: '12px 28px',
          borderRadius: '9999px',
          fontWeight: 600,
          textDecoration: 'none',
          fontSize: '15px',
        }}>
          ← Back to results
        </a>
      </div>
    )
  }

  const studentName = diagnostic.students?.name ?? 'Student'

  return (
    <MatchesClient
      id={id}
      studentName={studentName}
      matches={matches}
    />
  )
}
