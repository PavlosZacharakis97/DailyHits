import { GuessHistory } from './components/GuessHistory.jsx'
import { Header } from './components/Header.jsx'
import { NotFound } from './components/NotFound.jsx'
import { PuzzleCard } from './components/PuzzleCard.jsx'
import { ConsentGate } from './consent/ConsentGate.jsx'
import { useGame } from './game/useGame.js'
import styles from './App.module.css'

function App() {
  // The game lives on "/" only; any other path is a 404 (no cookies needed there).
  const isHome = window.location.pathname === '/'

  return (
    <>
      <Header />
      {isHome ? (
        <ConsentGate>
          <Game />
        </ConsentGate>
      ) : (
        <NotFound />
      )}
    </>
  )
}

/** Mounted only after cookie consent, so no game request happens before it. */
function Game() {
  const game = useGame()

  if (game.loadError) {
    const noPuzzle = game.loadError.code === 'puzzle_not_found'
    return (
      <main className={styles.main}>
        <section className={styles.message} role="alert">
          <h1 className={styles.messageTitle}>
            {noPuzzle ? 'No song today… yet' : 'We could not load the game'}
          </h1>
          <p className={styles.messageText}>
            {noPuzzle ? 'Today’s song is not ready. Please come back a little later.' : game.loadError.message}
          </p>
          <button type="button" className={styles.retry} onClick={() => window.location.reload()}>
            Try again
          </button>
        </section>
      </main>
    )
  }

  if (game.loading) {
    return (
      <main className={styles.main} aria-busy="true">
        <p className={styles.loading}>Loading today’s song…</p>
      </main>
    )
  }

  return (
    <main className={styles.main}>
      <PuzzleCard game={game} />
      <GuessHistory guesses={game.guesses} />
    </main>
  )
}

export default App
