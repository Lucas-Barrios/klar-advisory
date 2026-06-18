import { ImageResponse } from 'next/og'

export const size = { width: 32, height: 32 }
export const contentType = 'image/png'

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#2563EB',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '7px',
        }}
      >
        <div
          style={{
            color: 'white',
            fontSize: 22,
            fontWeight: 700,
            fontFamily: 'Space Grotesk, system-ui, sans-serif',
            lineHeight: 1,
          }}
        >
          K
        </div>
      </div>
    ),
    { ...size }
  )
}
