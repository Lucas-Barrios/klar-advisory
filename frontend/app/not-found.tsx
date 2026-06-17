'use client'
import Link from 'next/link'

export default function NotFound() {
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
      <div style={{ fontSize: '64px', marginBottom: '16px' }}>🗺️</div>
      <h1 style={{
        fontSize: '48px',
        fontWeight: 700,
        color: '#F9FAFB',
        letterSpacing: '-0.03em',
        margin: 0
      }}>404</h1>
      <p style={{
        fontSize: '18px',
        color: '#9CA3AF',
        marginTop: '12px',
        marginBottom: '32px'
      }}>
        This page does not exist — but Germany does.
      </p>
      <Link href="/" style={{
        background: 'var(--accent)',
        color: 'white',
        padding: '12px 28px',
        borderRadius: '9999px',
        fontWeight: 600,
        textDecoration: 'none',
        fontSize: '15px'
      }}>
        Back to Klar →
      </Link>
    </div>
  )
}
