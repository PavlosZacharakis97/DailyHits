import { useEffect } from 'react'
import { Vinyl } from './Vinyl.jsx'
import styles from './NotFound.module.css'

const SAD_NOTES = ['♪', '♫', '♬', '♪']

/** “Track not found”: a scratched record stands in for the 0 in 404. */
export function NotFound() {
  useEffect(() => {
    document.title = 'Page not found – dailyhit'
  }, [])

  const path = decodeURIComponent(window.location.pathname)
  const canGoBack = window.history.length > 1

  return (
    <main className={styles.page} aria-labelledby="not-found-title">
      <div className={styles.scene} aria-hidden="true">
        <span className={`${styles.digit} gradient-text`}>4</span>

        <div className={styles.deck}>
          <div className={styles.platter}>
            <Vinyl className={styles.record} label="404" />
          </div>
          <svg className={styles.arm} viewBox="0 0 120 160">
            <circle cx="96" cy="20" r="14" fill="var(--surface)" stroke="var(--divider)" strokeWidth="3" />
            <circle cx="96" cy="20" r="5" fill="var(--text-strong)" />
            <path d="M96 20 L92 112 Q90 128 74 136" fill="none" stroke="var(--muted)" strokeWidth="6" strokeLinecap="round" />
            <rect x="58" y="128" width="24" height="16" rx="4" transform="rotate(-28 70 136)" fill="var(--text-strong)" />
          </svg>
          {SAD_NOTES.map((note, i) => (
            <span key={i} className={styles.note} style={{ '--i': i }}>
              {note}
            </span>
          ))}
        </div>

        <span className={`${styles.digit} gradient-text`}>4</span>
      </div>

      <svg className={styles.wave} viewBox="0 0 600 60" preserveAspectRatio="none" aria-hidden="true">
        <path
          className={styles.wavePath}
          d="M0 30 H170 L185 12 L200 48 L215 6 L230 54 L245 18 L260 42 L275 26 L290 34 L305 29 L320 31 H600"
        />
      </svg>

      <h1 id="not-found-title" className={styles.title}>
        This track isn’t on the record
      </h1>
      <p className={styles.text}>
        The needle skipped a groove. <code className={styles.path}>{path}</code> was never released
        — maybe it was a B-side.
      </p>

      <div className={styles.actions}>
        <a className={styles.primary} href="/">
          Play today’s song
        </a>
        {canGoBack && (
          <button type="button" className={styles.secondary} onClick={() => window.history.back()}>
            Go back
          </button>
        )}
      </div>
    </main>
  )
}
