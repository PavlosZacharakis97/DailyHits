import styles from './Panels.module.css'

/** Horizontal bars: how many wins took 1, 2, … 10 guesses. */
export function Distribution({ distribution, highlight }) {
  const max = Math.max(1, ...distribution)
  return (
    <ol className={styles.dist} aria-label="Wins by number of guesses">
      {distribution.map((count, i) => (
        <li key={i} className={styles.distRow}>
          <span className={styles.distLabel}>{i + 1}</span>
          <span className={styles.distTrack}>
            <span
              className={styles.distBar}
              data-current={highlight === i + 1 || undefined}
              style={{ '--w': `${Math.max(8, (count / max) * 100)}%` }}
            >
              {count}
            </span>
          </span>
        </li>
      ))}
    </ol>
  )
}

export function StatGrid({ stats }) {
  const items = [
    ['Played', stats.played],
    ['Win %', stats.winRate],
    ['Streak', stats.currentStreak],
    ['Best', stats.maxStreak],
  ]
  return (
    <dl className={styles.statGrid}>
      {items.map(([label, value]) => (
        <div key={label} className={styles.stat}>
          <dt className={styles.statLabel}>{label}</dt>
          <dd className={`${styles.statValue} display`}>{value}</dd>
        </div>
      ))}
    </dl>
  )
}
