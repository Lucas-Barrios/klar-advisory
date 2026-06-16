import TrackerClient from './TrackerClient'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

type RoadmapStep = {
  month: number
  title: string
  description: string
  action_items: string[]
}

type PublicDiagnosticResult = {
  status: string
  roadmap?: RoadmapStep[] | null
  completed_steps?: number[] | null
  student?: {
    name?: string | null
  } | null
  students?: {
    name?: string | null
    full_name?: string | null
  } | null
}

export default async function TrackerPage(props: PageProps<'/tracker/[id]'>) {
  const { id } = await props.params

  let data: PublicDiagnosticResult | null = null
  let error = false

  try {
    const res = await fetch(`${API_URL}/api/diagnostic/${id}/result`, {
      cache: 'no-store',
    })
    if (!res.ok) {
      error = true
    } else {
      data = await res.json()
    }
  } catch {
    error = true
  }

  if (error || !data) {
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
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
        <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#F9FAFB', margin: 0 }}>
          Diagnostic not found
        </h2>
        <p style={{ color: '#9CA3AF', marginTop: '12px', maxWidth: '360px', lineHeight: 1.6 }}>
          This diagnostic ID does not exist or has not been submitted yet.
        </p>
        <a href="/diagnostic" style={{
          marginTop: '32px',
          background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
          color: 'white',
          padding: '12px 28px',
          borderRadius: '9999px',
          fontWeight: 600,
          textDecoration: 'none',
          fontSize: '15px',
        }}>
          Start a new diagnostic →
        </a>
      </div>
    )
  }

  if (data.status !== 'approved') {
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
          Tracker not yet available
        </h2>
        <p style={{ color: '#9CA3AF', marginTop: '12px', maxWidth: '400px', lineHeight: 1.6 }}>
          Your tracker will be available once your diagnostic is approved. Check back after you
          receive your results by email.
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

  const studentName =
    data.students?.name
    ?? data.students?.full_name
    ?? data.student?.name
    ?? 'Student'
  const roadmap = data.roadmap ?? []
  const initialCompleted = data.completed_steps ?? []

  return (
    <TrackerClient
      diagnosticId={id}
      studentName={studentName}
      roadmap={roadmap}
      initialCompleted={initialCompleted}
      apiUrl={API_URL}
    />
  )
}
