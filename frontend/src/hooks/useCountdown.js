import { useEffect, useState } from 'react'

const pad = (n) => String(n).padStart(2, '0')

/** “hh:mm:ss” until `target` (ms timestamp), ticking every second. */
export function useCountdown(target) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])

  const left = Math.max(0, target - now)
  const s = Math.floor(left / 1000)
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`
}
