import { useEffect, useState } from 'react'

const pad = (n) => String(n).padStart(2, '0')

/** Time left until `target` (ms timestamp), ticking every second. */
export function useCountdown(target) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])

  const left = Math.max(0, target - now)
  const s = Math.floor(left / 1000)
  const hours = Math.floor(s / 3600)
  const minutes = Math.floor((s % 3600) / 60)
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
  return {
    done: left === 0,
    text: `${pad(hours)}:${pad(minutes)}:${pad(s % 60)}`,
    // Spoken form for screen readers, e.g. “1 hour 12 minutes”.
    spoken: `${plural(hours, 'hour')} ${plural(minutes, 'minute')}`,
  }
}
