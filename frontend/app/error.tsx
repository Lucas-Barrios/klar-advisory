'use client'
import { useEffect } from 'react'
import Link from 'next/link'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

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
      <div style={{ fontSize: '64px', marginBottom: '16px' }}>⚡</div>
      <h1 style={{
        fontSize: '32px',
        fontWeight: 700,
        color: '#F9FAFB',
        letterSpacing: '-0.02em',
        margin: 0
      }}>Something went wrong</h1>
      <p style={{
        fontSize: '16px',
        color: '#9CA3AF',
        marginTop: '12px',
        marginBottom: '32px',
        maxWidth: '400px'
      }}>
        An unexpected error occurred. Your diagnostic data is safe —
        try refreshing or go back to the homepage.
      </p>
      <div style={{ display: 'flex', gap: '12px' }}>
        <button
          onClick={reset}
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#F9FAFB',
            padding: '10px 24px',
            borderRadius: '9999px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Try again
        </button>
        <Link href="/" style={{
          background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
          color: 'white',
          padding: '10px 24px',
          borderRadius: '9999px',
          fontWeight: 600,
          textDecoration: 'none',
          fontSize: '14px'
        }}>
          Back to Klar
        </Link>
      </div>
    </div>
  )
}
