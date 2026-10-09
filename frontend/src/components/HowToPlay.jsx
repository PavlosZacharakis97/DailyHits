import { Modal } from './Modal.jsx'
import styles from './Panels.module.css'

const EXAMPLES = [
  { label: 'Genre', value: 'Rock', color: 'green', note: 'Same genre.' },
  { label: 'Year', value: '1977 ↑', color: 'yellow', note: 'Within 5 years — the answer is later.' },
  { label: 'Country', value: 'Sweden', color: 'yellow', note: 'Same part of the world.' },
  { label: 'Artist', value: 'ABBA', color: 'gray', note: 'Not related.' },
]
const MARK = { green: '✓', yellow: '≈', gray: '✕' }

export function HowToPlay({ open, onClose }) {
  return (
    <Modal open={open} onClose={onClose} title="How to play">
      <ol className={styles.steps}>
        <li>
          <strong>Guess today’s hit in 10 tries.</strong> Type a song and pick it from the list.
        </li>
        <li>
          <strong>Every guess shows 8 tiles</strong>: artist, year, genre, style, vocal, theme,
          country and language of the song you tried.
        </li>
        <li>
          <strong>Colours tell you how close you are.</strong>
        </li>
      </ol>

      <ul className={styles.examples} role="list">
        {EXAMPLES.map((e) => (
          <li key={e.label} className={styles.example}>
            <span className={styles.exTile} data-color={e.color}>
              <span className={styles.exMark} aria-hidden="true">
                {MARK[e.color]}
              </span>
              <span className={styles.exLabel}>{e.label}</span>
              <span className={styles.exValue}>{e.value}</span>
            </span>
            <span className={styles.exNote}>{e.note}</span>
          </li>
        ))}
      </ul>

      <p className={styles.para}>
        <strong>Yellow means “almost”:</strong> a related genre, a style of the same genre, a theme
        of the same kind, or a shared band member — Freddie Mercury solo is close to Queen.
      </p>
      <p className={styles.para}>
        💡 Stuck? <strong>Hints</strong> unlock after guess 5 and guess 8. A new song arrives
        every day at midnight UTC.
      </p>
      <button type="button" className={styles.primary} onClick={onClose}>
        Let’s play
      </button>
    </Modal>
  )
}
