import { useEffect, useRef, useState } from 'react'
import { GuessHistory } from './components/GuessHistory.jsx'
import { Header } from './components/Header.jsx'
import { HowToPlay } from './components/HowToPlay.jsx'
import { NotFound } from './components/NotFound.jsx'
import { PuzzleCard } from './components/PuzzleCard.jsx'
import { ResultPanel } from './components/ResultPanel.jsx'
import { StatsPanel } from './components/StatsPanel.jsx'
import { ConsentGate } from './consent/ConsentGate.jsx'
import { useGame } from './game/useGame.js'
import styles from './App.module.css'

const HELP_SEEN = 'dh_help_seen'
const utcToday = () => new Date().toISOString().slice(0, 10)

function App() {
  // The game lives on "/" only; any other path is a 404 (no cookies needed there).
  const isHome = window.location.pathname === '/'
  const [panel, setPanel] = useState(null)
  const close = () => setPanel(null)

  if (!isHome) {
    return (
      <>
        <Header />
        <NotFound />
      </>
    )
  }

  return (
    <>
      <Header onHelp={() => setPanel('help')} onStats={() => setPanel('stats')} />
      <ConsentGate>
        <Game onFirstVisit={() => setPanel('help')} />
      </ConsentGate>
      <HowToPlay open={panel === 'help'} onClose={close} />
      <StatsPanel open={panel === 'stats'} onClose={close} today={utcToday()} />
    </>
  )
}

/** Mounted only after cookie consent, so no game request happens before it. */
function Game({ onFirstVisit }) {
  const game = useGame()
  const [showResult, setShowResult] = useState(false)
  const wasPlaying = useRef(null)

  useEffect(() => {
    try {
      if (!localStorage.getItem(HELP_SEEN)) {
        localStorage.setItem(HELP_SEEN, '1')
        onFirstVisit()
      }
    } catch {
      // No storage: skip the automatic tutorial.
    }
  }, [onFirstVisit])

  // Open the result sheet when the game ends during this visit (not on reload).
  const finished = !game.loading && game.status !== 'in_progress'
  useEffect(() => {
    if (game.loading) return
    if (wasPlaying.current === true && finished && game.answer) {
      if (game.status === 'won') navigator.vibrate?.([30, 60, 30])
      const timer = setTimeout(() => setShowResult(true), game.status === 'won' ? 1600 : 500)
      wasPlaying.current = false
      return () => clearTimeout(timer)
    }
    if (wasPlaying.current === null) wasPlaying.current = !finished
    return undefined
  }, [game.loading, finished, game.answer, game.status])

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
      <PuzzleCard game={game} onShowResult={() => setShowResult(true)} />
      <GuessHistory guesses={game.guesses} />
      {finished && (
        <ResultPanel open={showResult} onClose={() => setShowResult(false)} game={game} date={game.date} />
      )}
    </main>
  )
}

export default App
