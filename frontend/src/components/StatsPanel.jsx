import { computeStats } from '../game/stats.js'
import { Distribution, StatGrid } from './Distribution.jsx'
import { Modal } from './Modal.jsx'
import styles from './Panels.module.css'

export function StatsPanel({ open, onClose, today }) {
  const stats = computeStats(today)
  return (
    <Modal open={open} onClose={onClose} title="Your stats">
      <StatGrid stats={stats} />
      <h3 className={styles.subhead}>Guess distribution</h3>
      {stats.wins ? (
        <Distribution distribution={stats.distribution} />
      ) : (
        <p className={styles.para}>Win a game to see how many guesses you usually need.</p>
      )}
      <p className={styles.note}>
        Stats are kept in this browser. Sign-in to keep them everywhere is coming soon.
      </p>
    </Modal>
  )
}
