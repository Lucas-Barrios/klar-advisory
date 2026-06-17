export default function GermanFlag({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size * 0.6} viewBox="0 0 30 18" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
      <rect width="30" height="6" y="0" fill="#1A1A1A" />
      <rect width="30" height="6" y="6" fill="#DD0000" />
      <rect width="30" height="6" y="12" fill="#FFCC00" />
    </svg>
  )
}
