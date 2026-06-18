'use client'

import { AlertTriangle, X } from 'lucide-react'

interface ErrorMessageProps {
  message: string
  onDismiss?: () => void
  onRetry?: () => void
}

export default function ErrorMessage({ message, onDismiss, onRetry }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        background: 'rgba(245,158,11,0.1)',
        border: '1px solid rgba(245,158,11,0.3)',
        borderRadius: '12px',
        padding: '12px 14px',
        fontSize: '13px',
        color: '#FCD34D',
      }}
    >
      <AlertTriangle size={15} color="#F59E0B" style={{ flexShrink: 0, marginTop: '1px' }} />
      <span style={{ flex: 1, lineHeight: 1.5 }}>{message}</span>
      {(onRetry || onDismiss) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
          {onRetry && (
            <button
              onClick={onRetry}
              style={{
                background: 'rgba(245,158,11,0.15)',
                border: '1px solid rgba(245,158,11,0.35)',
                borderRadius: '6px',
                color: '#F59E0B',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 600,
                padding: '3px 10px',
                whiteSpace: 'nowrap',
              }}
            >
              Try again
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              aria-label="Dismiss"
              style={{
                background: 'none',
                border: 'none',
                color: '#9CA3AF',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '2px',
                lineHeight: 1,
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
