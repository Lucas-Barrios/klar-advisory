'use client'
import { useState, useEffect } from 'react'

export function useIsWide(breakpoint = 900): boolean {
  const [wide, setWide] = useState(true)
  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${breakpoint}px)`)
    setWide(mq.matches)
    const onChange = (e: MediaQueryListEvent) => setWide(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [breakpoint])
  return wide
}
