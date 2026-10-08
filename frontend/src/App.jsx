import { GuessHistory } from './components/GuessHistory.jsx'
import { Header } from './components/Header.jsx'
import { NotFound } from './components/NotFound.jsx'
import { PuzzleCard } from './components/PuzzleCard.jsx'
import { ConsentGate } from './consent/ConsentGate.jsx'
import { MAX_ATTEMPTS } from './game/rules.js'
import { useMockGame } from './mock/useMockGame.js'
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
  const game = useMockGame()

  return (
    <main className={styles.main}>
      <PuzzleCard game={game} maxAttempts={MAX_ATTEMPTS} />
      <GuessHistory guesses={game.guesses} />
    </main>
  )
}

export default App
