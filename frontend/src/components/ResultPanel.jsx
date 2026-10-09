import { useState } from 'react'
import { computeStats, nextPuzzleAt, pointsFor, shareText } from '../game/stats.js'
import { useCountdown } from '../hooks/useCountdown.js'
import { Distribution, StatGrid } from './Distribution.jsx'
import { PlayIcon } from './Icons.jsx'
import { Modal } from './Modal.jsx'
import styles from './Panels.module.css'

const TITLE = { won: 'You got it! 🎉', lost: 'So close!', gave_up: 'Next time!' }

export function ResultPanel({ open, onClose, game, date }) {
  const [copied, setCopied] = useState(false)
  const countdown = useCountdown(nextPuzzleAt(date))
  const stats = computeStats(date)
  const used = game.guesses.length
  const points = pointsFor(game.status, used)

  async function share() {
    const text = shareText({ ...game, number: game.number })
    try {
      if (navigator.share && matchMedia('(pointer: coarse)').matches) {
        await navigator.share({ text })
        return
      }
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Share sheet dismissed or clipboard blocked: nothing to do.
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={TITLE[game.status] ?? 'Results'} wide>
      {game.answer && (
        <div className={styles.answer}>
          <p className={`${styles.answerTitle} display`}>{game.answer.title}</p>
          <p className={styles.answerArtist}>
            {game.answer.artist}
            {game.answer.featured.length > 0 && ` feat. ${game.answer.featured.join(', ')}`} ·{' '}
            {game.answer.year}
          </p>
          <a className={styles.youtube} href={game.answer.youtube_url} target="_blank" rel="noopener">
            <PlayIcon size={14} /> Listen on YouTube
            <span className="visually-hidden"> (opens in a new tab)</span>
          </a>
        </div>
      )}

      <div className={styles.scoreRow}>
        <div className={styles.score}>
          <span className={`${styles.scoreValue} display`}>{points}</span>
          <span className={styles.scoreLabel}>points today</span>
        </div>
        <div className={styles.next}>
          <span className={styles.scoreLabel}>Next song in</span>
          <span className={`${styles.countdown} display`} aria-live="off">
            {countdown}
          </span>
        </div>
      </div>

      <button type="button" className={styles.primary} onClick={share}>
        {copied ? 'Copied! Paste it anywhere' : 'Share result'}
      </button>
      <span className="visually-hidden" role="status">
        {copied ? 'Result copied to the clipboard.' : ''}
      </span>

      <StatGrid stats={stats} />
      <h3 className={styles.subhead}>Guess distribution</h3>
      {stats.wins ? (
        <Distribution
          distribution={stats.distribution}
          highlight={game.status === 'won' ? used : undefined}
        />
      ) : (
        <p className={styles.para}>Win a game to see how many guesses you usually need.</p>
      )}
    </Modal>
  )
}
