import { COLOR_LABEL, COLOR_MARK, TILES } from './tiles.js'
import styles from './GuessHistory.module.css'

const ARROW = { up: '↑', down: '↓' }
const DIRECTION_LABEL = { up: 'the answer is later', down: 'the answer is earlier' }

export function GuessHistory({ guesses }) {
  if (guesses.length === 0) {
    return (
      <p className={styles.empty}>
        Pick any song to start. Green ✓ means a match, yellow ≈ means close, gray ✕ means no match.
      </p>
    )
  }

  return (
    <section className={styles.history} aria-labelledby="guesses-title">
      <h2 id="guesses-title" className="visually-hidden">
        Your guesses
      </h2>
      <ol className={styles.list} role="list">
        {[...guesses].reverse().map(({ song, tiles }, index) => (
          <li key={song.id} className={styles.row} data-latest={index === 0 || undefined}>
            <p className={styles.song}>
              <span className={styles.number}>
                <span className="visually-hidden">Guess </span>
                {guesses.length - index}
              </span>
              <span className={styles.songTitle}>{song.title}</span>
              <span className={styles.songArtist}>{song.artist}</span>
            </p>
            <ul className={styles.tiles} role="list">
              {tiles.map((tile) => {
                const { label } = TILES.find((t) => t.key === tile.key)
                return (
                  <li key={tile.key} className={styles.tile} data-color={tile.color}>
                    <span className={styles.mark} aria-hidden="true">
                      {COLOR_MARK[tile.color]}
                    </span>
                    <span className={styles.label}>{label}</span>
                    <span className={styles.value}>
                      {tile.value}
                      {tile.direction && <span aria-hidden="true"> {ARROW[tile.direction]}</span>}
                    </span>
                    <span className="visually-hidden">
                      , {COLOR_LABEL[tile.color]}
                      {tile.direction && `, ${DIRECTION_LABEL[tile.direction]}`}
                    </span>
                  </li>
                )
              })}
            </ul>
          </li>
        ))}
      </ol>
    </section>
  )
}
