'use client'

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

type MatchesData = {
  matched_positions: MatchedPosition[]
  reasoning_summary: string | null
  status: string
} | null

export default function MatchesClient({
  id,
  studentName,
  matches,
}: {
  id: string
  studentName: string
  matches: MatchesData
}) {
  const positions = matches?.matched_positions ?? []
  const firstName = studentName.split(' ')[0]

  return (
    <div style={{ background: '#0A0E1A', minHeight: '100vh' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto', padding: '48px 16px 80px' }}>

        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <a
            href={`/results/${id}`}
            style={{ fontSize: '0.875rem', color: '#6B7280', textDecoration: 'none' }}
          >
            ← Back to results
          </a>
          <h1
            style={{
              fontSize: '2rem',
              fontWeight: 700,
              color: '#F9FAFB',
              letterSpacing: '-0.02em',
              marginTop: '16px',
              marginBottom: '4px',
            }}
          >
            {firstName}&apos;s Matched Positions
          </h1>
          <p style={{ color: '#9CA3AF', fontSize: '0.9375rem' }}>
            Real Ausbildung openings matched to your profile
          </p>
        </div>

        {/* Disclosure banner */}
        <div
          style={{
            background: 'rgba(59,130,246,0.07)',
            border: '1px solid rgba(59,130,246,0.2)',
            borderRadius: '12px',
            padding: '14px 16px',
            marginBottom: '32px',
            fontSize: '0.8125rem',
            color: '#93C5FD',
            lineHeight: 1.6,
          }}
        >
          These are real, currently open Ausbildung positions from Germany&apos;s Federal
          Employment Agency, refreshed regularly. German language requirements shown are
          AI-estimated based on occupation type — always confirm directly with the employer.
        </div>

        {/* Summary */}
        {matches?.reasoning_summary && (
          <p
            style={{
              color: '#9CA3AF',
              fontSize: '0.9375rem',
              lineHeight: 1.7,
              marginBottom: '32px',
            }}
          >
            {matches.reasoning_summary}
          </p>
        )}

        {/* No positions state */}
        {positions.length === 0 && (
          <div
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid #1F2937',
              borderRadius: '16px',
              padding: '48px 24px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>🔍</div>
            <p style={{ color: '#F9FAFB', fontWeight: 600, marginBottom: '8px' }}>
              No positions available yet
            </p>
            <p style={{ color: '#6B7280', fontSize: '0.875rem' }}>
              Position matching is in progress. Check back shortly.
            </p>
          </div>
        )}

        {/* Position cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {positions.map((pos, i) => {
            const hasConcern =
              pos.german_level_concern === true || pos.german_level_concern === 'true'

            return (
              <div
                key={pos.refnr ?? i}
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid #1F2937',
                  borderRadius: '16px',
                  padding: '24px',
                }}
              >
                {/* Card header */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    gap: '12px',
                    flexWrap: 'wrap',
                  }}
                >
                  <div>
                    <p
                      style={{
                        fontSize: '1.0625rem',
                        fontWeight: 700,
                        color: '#F9FAFB',
                        margin: 0,
                      }}
                    >
                      {pos.arbeitgeber ?? 'Employer not specified'}
                    </p>
                    <p style={{ fontSize: '0.9375rem', color: '#9CA3AF', marginTop: '4px' }}>
                      {pos.titel ?? 'Position'} &mdash; {pos.ort ?? 'Location not specified'}
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', flexShrink: 0 }}>
                    <span
                      style={{
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        padding: '4px 12px',
                        background: 'rgba(59,130,246,0.12)',
                        color: '#60A5FA',
                        border: '1px solid rgba(59,130,246,0.25)',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {pos.estimated_german_level_needed}+ required (est.)
                    </span>
                    {hasConcern && (
                      <span
                        style={{
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          padding: '4px 12px',
                          background: 'rgba(239,68,68,0.12)',
                          color: '#F87171',
                          border: '1px solid rgba(239,68,68,0.3)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        ⚠ Level may be insufficient
                      </span>
                    )}
                  </div>
                </div>

                {/* Fit explanation */}
                <p
                  style={{
                    color: '#9CA3AF',
                    fontSize: '0.9375rem',
                    lineHeight: 1.7,
                    marginTop: '14px',
                  }}
                >
                  {pos.fit_explanation}
                </p>

                {/* Footer row */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '16px',
                    flexWrap: 'wrap',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    {pos.eintrittsdatum && (
                      <span style={{ fontSize: '0.8125rem', color: '#6B7280' }}>
                        📅 Start: {pos.eintrittsdatum}
                      </span>
                    )}
                    {pos.urgency_note && (
                      <span style={{ fontSize: '0.8125rem', color: '#6B7280' }}>
                        {pos.urgency_note}
                      </span>
                    )}
                  </div>

                  {pos.application_url && (
                    <a
                      href={pos.application_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                        color: 'white',
                        padding: '10px 20px',
                        borderRadius: '9999px',
                        fontWeight: 600,
                        textDecoration: 'none',
                        fontSize: '0.875rem',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      Apply on Bundesagentur →
                    </a>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer disclaimer */}
        {positions.length > 0 && (
          <p
            style={{
              fontSize: '0.75rem',
              color: '#4B5563',
              textAlign: 'center',
              marginTop: '48px',
              lineHeight: 1.6,
            }}
          >
            Position data sourced from the Bundesagentur für Arbeit public API.
            Always verify requirements directly with the employer before applying.
          </p>
        )}
      </div>
    </div>
  )
}
