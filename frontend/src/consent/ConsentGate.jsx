import { useEffect, useRef, useState } from 'react'
import { COOKIES, clearConsent, readConsent, saveConsent } from './consent.js'
import styles from './ConsentGate.module.css'

/**
 * Blocks the game until the player accepts the essential cookies.
 * Children are not rendered before that, so no game request is ever made.
 */
export function ConsentGate({ children }) {
  const [choice, setChoice] = useState(() => (readConsent() ? 'accepted' : 'undecided'))

  if (choice === 'accepted') {
    return (
      <>
        {children}
        <footer className={styles.footer}>
          <button
            type="button"
            className={styles.link}
            onClick={() => {
              clearConsent()
              setChoice('undecided')
            }}
          >
            Cookie settings
          </button>
        </footer>
      </>
    )
  }

  return (
    <ConsentDialog
      declined={choice === 'declined'}
      onAccept={() => {
        saveConsent()
        setChoice('accepted')
        // Put the player straight into the guess field once the game renders.
        requestAnimationFrame(() => document.querySelector('input[role="combobox"]')?.focus())
      }}
      onDecline={() => setChoice('declined')}
      onReconsider={() => setChoice('undecided')}
    />
  )
}

function ConsentDialog({ declined, onAccept, onDecline, onReconsider }) {
  const [details, setDetails] = useState(false)
  const primary = useRef(null)

  useEffect(() => {
    primary.current?.focus()
  }, [declined])

  if (declined) {
    return (
      <div className={styles.backdrop}>
        <section className={styles.dialog} role="alertdialog" aria-modal="true" aria-labelledby="consent-title" aria-describedby="consent-text">
          <span className={styles.emoji} aria-hidden="true">🍪</span>
          <h1 id="consent-title" className={styles.title}>Cookies are needed to play</h1>
          <p id="consent-text" className={styles.text}>
            dailyhit keeps your guesses on our server so nobody can peek at the answer. That needs
            one anonymous cookie. Without it the game can’t start.
          </p>
          <div className={styles.actions}>
            <button ref={primary} type="button" className={styles.accept} onClick={onReconsider}>
              Review my choice
            </button>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className={styles.backdrop}>
      <section className={styles.dialog} role="dialog" aria-modal="true" aria-labelledby="consent-title" aria-describedby="consent-text">
        <span className={styles.emoji} aria-hidden="true">🍪</span>
        <h1 id="consent-title" className={styles.title}>Before you play</h1>
        <p id="consent-text" className={styles.text}>
          dailyhit uses only essential cookies: they save your progress for today’s song.
          No ads, no tracking, no third parties.
        </p>

        <button
          type="button"
          className={styles.link}
          aria-expanded={details}
          aria-controls="consent-details"
          onClick={() => setDetails((d) => !d)}
        >
          {details ? 'Hide details' : 'What we store'}
        </button>
        {details && (
          <table id="consent-details" className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Cookie</th>
                <th scope="col">Why</th>
                <th scope="col">Kept for</th>
              </tr>
            </thead>
            <tbody>
              {COOKIES.map((c) => (
                <tr key={c.name}>
                  <td><code>{c.name}</code></td>
                  <td>{c.purpose}</td>
                  <td>{c.lifetime}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {details && (
          <p className={styles.note}>
            Your theme choice is saved only in your browser and is never sent to us.
          </p>
        )}

        <div className={styles.actions}>
          <button type="button" className={styles.decline} onClick={onDecline}>
            Decline
          </button>
          <button ref={primary} type="button" className={styles.accept} onClick={onAccept}>
            Accept and play
          </button>
        </div>
      </section>
    </div>
  )
}
