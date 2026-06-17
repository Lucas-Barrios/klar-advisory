import { LucideIcon } from 'lucide-react'

interface LevelIndicatorProps {
  icon: LucideIcon
  filled: number
  total: number
}

export default function LevelIndicator({ icon: Icon, filled, total }: LevelIndicatorProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <Icon size={18} color="var(--text2)" style={{ flexShrink: 0 }} />
      <div style={{ display: 'flex', gap: '3px' }}>
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            style={{
              width: '14px',
              height: '4px',
              borderRadius: '2px',
              background: i < filled ? 'var(--accent)' : 'var(--bg3)'
            }}
          />
        ))}
      </div>
    </div>
  )
}
