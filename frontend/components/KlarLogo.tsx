type Size = 'sm' | 'md' | 'lg'

const sizeMap: Record<Size, number> = { sm: 18, md: 24, lg: 36 }

export default function KlarLogo({ color = '#F9FAFB', size = 'md' }: { color?: string; size?: Size }) {
  const h = sizeMap[size]
  const w = Math.round(h * 72 / 28)

  return (
    <svg
      width={w}
      height={h}
      viewBox="0 0 72 28"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Klar"
      role="img"
    >
      <text
        x="0"
        y="22"
        fill={color}
        style={{
          fontFamily: 'Space Grotesk, system-ui, sans-serif',
          fontWeight: 700,
          fontSize: '24px',
          letterSpacing: '-0.04em',
        }}
      >
        Klar
      </text>
      {/* Three dots in diagonal arrangement after final "r" — suggest a path or journey */}
      <circle cx="56" cy="12" r="2" fill="#2563EB" />
      <circle cx="61" cy="16" r="2" fill="#2563EB" />
      <circle cx="66" cy="20" r="2" fill="#2563EB" />
    </svg>
  )
}
