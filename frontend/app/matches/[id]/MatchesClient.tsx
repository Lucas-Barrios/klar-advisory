'use client'

import { useState } from 'react'
import { Search, Clock, Lock } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

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
  matches_unlocked?: boolean
  locked_count?: number
} | null

export default function MatchesClient({
  id,
  studentName,
  matches,
  paymentSuccess = false,
}: {
  id: string
  studentName: string
  matches: MatchesData
  paymentSuccess?: boolean
}) {
  const [checkoutLoading, setCheckoutLoading] = useState(false)

  const positions = matches?.matched_positions ?? []
  const lockedCount = matches?.locked_count ?? 0
  const isLocked = !matches?.matches_unlocked && lockedCount > 0
  const firstName = studentName.split(' ')[0]

  const handleUnlock = async () => {
    setCheckoutLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/payments/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diagnostic_id: id, product: 'matches' }),
      })
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      } else {
        setCheckoutLoading(false)
      }
    } catch {
      setCheckoutLoading(false)
    }
  }

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

        {/* Payment success banner */}
        {paymentSuccess && (
          <div style={{
            background: 'rgba(13,148,136,0.1)',
            border: '1px solid rgba(13,148,136,0.3)',
            borderRadius: '12px',
            padding: '14px 16px',
            marginBottom: '24px',
            fontSize: '0.875rem',
            color: 'var(--accent-light)',
          }}>
            Payment successful — all your matched positions are now unlocked.
          </div>
        )}

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
        {positions.length === 0 && !isLocked && (
          <div
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid #1F2937',
              borderRadius: '16px',
              padding: '48px 24px',
              textAlign: 'center',
            }}
          >
            <div style={{ marginBottom: '16px' }}><Search size={40} color="#6B7280" /></div>
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
                        color: 'var(--accent-light)',
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
                        ⚠ German level may be insufficient
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
                      <span style={{ fontSize: '0.8125rem', color: '#6B7280', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} /> Start: {pos.eintrittsdatum}
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
                        background: 'var(--accent)',
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

          {/* Locked placeholder cards */}
          {isLocked && Array.from({ length: lockedCount }).map((_, i) => (
            <div
              key={`locked-${i}`}
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '16px',
                padding: '24px',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div style={{
                position: 'absolute',
                inset: 0,
                backdropFilter: 'blur(4px)',
                background: 'rgba(10,14,26,0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '16px',
              }}>
                <Lock size={20} color="#6B7280" />
              </div>
              {/* Ghost content */}
              <div style={{ height: '20px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', width: '40%', marginBottom: '8px' }} />
              <div style={{ height: '14px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', width: '60%', marginBottom: '16px' }} />
              <div style={{ height: '14px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', width: '80%', marginBottom: '6px' }} />
              <div style={{ height: '14px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', width: '70%' }} />
            </div>
          ))}
        </div>

        {/* Paywall CTA */}
        {isLocked && (
          <div style={{
            marginTop: '32px',
            background: 'rgba(13,148,136,0.06)',
            border: '1px solid rgba(13,148,136,0.2)',
            borderRadius: '20px',
            padding: '32px 24px',
            textAlign: 'center',
          }}>
            <div style={{ marginBottom: '8px' }}>
              <Lock size={28} color="var(--accent)" style={{ display: 'inline-block' }} />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#F9FAFB', margin: '0 0 8px' }}>
              {lockedCount} more position{lockedCount !== 1 ? 's' : ''} matched to your profile
            </h3>
            <p style={{ color: '#9CA3AF', fontSize: '0.9375rem', marginBottom: '24px', maxWidth: '440px', margin: '0 auto 24px' }}>
              Unlock all {positions.length + lockedCount} matched Ausbildung positions — real openings, sourced from Germany&apos;s Federal Employment Agency.
            </p>
            <button
              onClick={handleUnlock}
              disabled={checkoutLoading}
              style={{
                background: 'var(--accent)',
                color: 'white',
                padding: '14px 32px',
                borderRadius: '9999px',
                fontWeight: 700,
                fontSize: '1rem',
                border: 'none',
                cursor: checkoutLoading ? 'wait' : 'pointer',
                opacity: checkoutLoading ? 0.7 : 1,
              }}
            >
              {checkoutLoading ? 'Redirecting…' : `Unlock all ${positions.length + lockedCount} matches — €19`}
            </button>
          </div>
        )}

        {/* Footer disclaimer */}
        {positions.length > 0 && !isLocked && (
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
