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
        {/* Wordmark */}
        <div
          style={{
            color: '#F9FAFB',
            fontSize: 96,
            fontWeight: 800,
            letterSpacing: '-0.04em',
            fontFamily: 'Space Grotesk, system-ui, sans-serif',
            lineHeight: 1,
            marginBottom: 28,
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
