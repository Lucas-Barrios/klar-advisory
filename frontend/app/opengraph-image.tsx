import { ImageResponse } from 'next/og'

export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#0A0E1A',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        {/* Logo mark */}
        <div
          style={{
            background: '#2563EB',
            width: 96,
            height: 96,
            borderRadius: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 28,
          }}
        >
          <div style={{ color: 'white', fontSize: 60, fontWeight: 700, lineHeight: 1 }}>K</div>
        </div>

        {/* Title */}
        <div
          style={{
            color: '#F9FAFB',
            fontSize: 72,
            fontWeight: 700,
            letterSpacing: '-3px',
            marginBottom: 16,
          }}
        >
          Klar
        </div>

        {/* Tagline */}
        <div
          style={{
            color: '#9CA3AF',
            fontSize: 28,
            letterSpacing: '-0.5px',
          }}
        >
          Your clear path to Germany
        </div>

        {/* Blue accent bar */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 8,
            background: '#2563EB',
          }}
        />
      </div>
    ),
    { ...size }
  )
}
