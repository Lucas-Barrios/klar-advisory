type Size = 'sm' | 'md' | 'lg'

const sizeMap: Record<Size, number> = { sm: 18, md: 24, lg: 36 }

export default function KlarLogo({ size = 'md' }: { size?: Size }) {
  const h = sizeMap[size]
  const w = Math.round(h * 80 / 32)
  const gradientId = `klar-gradient-${size}`

  return (
    <svg
      width={w}
      height={h}
      viewBox="0 0 80 32"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Klar"
      role="img"
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#F9FAFB" />
          <stop offset="55%" stopColor="#F9FAFB" />
          <stop offset="100%" stopColor="#60A5FA" />
        </linearGradient>
      </defs>
      <text
        x="0"
        y="26"
        fill={`url(#${gradientId})`}
        style={{
          fontFamily: 'Space Grotesk, system-ui, sans-serif',
          fontWeight: 700,
          fontSize: '28px',
          letterSpacing: '-0.04em',
        }}
      >
        Klar
      </text>
    </svg>
  )
}
