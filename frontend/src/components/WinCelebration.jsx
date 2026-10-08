import { Vinyl } from './Vinyl.jsx'
import styles from './WinCelebration.module.css'

const COLORS = ['var(--accent)', 'var(--accent-2)', 'var(--art-sun)', 'var(--ic-mint-fg)', 'var(--ic-sky-fg)']
const NOTES = ['♪', '♫', '♬']

// Fixed, evenly spread burst (no randomness, so every render looks the same).
const PIECES = Array.from({ length: 28 }, (_, i) => {
  const angle = (i / 28) * Math.PI * 2 + (i % 2) * 0.2
  const distance = 120 + (i % 5) * 34
  return {
    x: Math.round(Math.cos(angle) * distance),
    y: Math.round(Math.sin(angle) * distance - 40),
    rotate: (i * 47) % 360,
    delay: (i % 7) * 0.03,
    color: COLORS[i % COLORS.length],
    note: i % 4 === 0 ? NOTES[(i / 4) % NOTES.length] : null,
  }
})

/** Spinning vinyl with floating notes and a one-off confetti burst, shown on a win. */
export function WinCelebration() {
  return (
    <div className={styles.stage} aria-hidden="true">
      <Vinyl className={styles.vinyl} />

      {NOTES.map((note, i) => (
        <span key={note} className={styles.float} style={{ '--i': i }}>
          {note}
        </span>
      ))}

      <div className={styles.burst}>
        {PIECES.map((p, i) => (
          <span
            key={i}
            className={p.note ? styles.noteBit : styles.bit}
            style={{
              '--x': `${p.x}px`,
              '--y': `${p.y}px`,
              '--r': `${p.rotate}deg`,
              '--d': `${p.delay}s`,
              '--c': p.color,
            }}
          >
            {p.note}
          </span>
        ))}
      </div>
    </div>
  )
}
