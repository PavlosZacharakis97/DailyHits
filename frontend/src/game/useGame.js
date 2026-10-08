import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client.js'

const CACHE_PREFIX = 'dh_game:'

// Last known state, so a returning player sees their board instantly while the
// server (always the source of truth) is asked again.
function readCache(key) {
  try {
    const cached = JSON.parse(localStorage.getItem(CACHE_PREFIX + key) ?? 'null')
    const today = new Date().toISOString().slice(0, 10)
    return cached?.state?.date === today ? cached : null
  } catch {
    return null
  }
}

function writeCache(key, value) {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(value))
  } catch {
    // Storage full or disabled: the game still works, just without the instant reload.
  }
}

const ERROR_TEXT = {
  throttled: 'Easy there! Wait a few seconds and try again.',
  already_guessed: 'You have already tried that song.',
  unknown_song: 'Pick a song from the list.',
  game_over: 'This game is already over.',
}

export function useGame({ edition = 'world', day = 'today' } = {}) {
  const key = `${edition}:${day}`
  const [state, setState] = useState(() => readCache(key)?.state ?? null)
  const [answer, setAnswer] = useState(() => readCache(key)?.answer ?? null)
  const [loadError, setLoadError] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [busy, setBusy] = useState(false)

  const finished = state && state.status !== 'in_progress'

  useEffect(() => {
    let cancelled = false
    api.puzzle(day, edition).then(
      (fresh) => !cancelled && setState(fresh),
      (error) => !cancelled && setLoadError(error),
    )
    return () => {
      cancelled = true
    }
  }, [day, edition])

  // The answer comes only from /reveal, and only once the game is over.
  useEffect(() => {
    if (!finished || answer) return undefined
    let cancelled = false
    api.reveal(day, edition).then((data) => !cancelled && setAnswer(data), () => {})
    return () => {
      cancelled = true
    }
  }, [finished, answer, day, edition])

  useEffect(() => {
    if (state) writeCache(key, { state, answer })
  }, [key, state, answer])

  const search = useCallback((q, signal) => api.search(q, edition, signal), [edition])

  async function guess(song) {
    if (busy || !state || finished) return
    setBusy(true)
    setActionError(null)
    try {
      const result = await api.guess(day, edition, song.id)
      setState((prev) => ({
        ...prev,
        status: result.status,
        attempts_used: result.attempts_used,
        attempts_left: result.attempts_left,
        hints: result.hints,
        guesses: [...prev.guesses, result.guess],
      }))
    } catch (error) {
      setActionError(ERROR_TEXT[error.code] ?? error.message)
    } finally {
      setBusy(false)
    }
  }

  async function giveUp() {
    if (busy || !state || finished) return
    setBusy(true)
    setActionError(null)
    try {
      setState(await api.giveUp(day, edition))
    } catch (error) {
      setActionError(ERROR_TEXT[error.code] ?? error.message)
    } finally {
      setBusy(false)
    }
  }

  return {
    loading: !state && !loadError,
    loadError,
    actionError,
    busy,
    number: state?.number,
    maxAttempts: state?.max_attempts ?? 10,
    yearYellowRange: state?.year_yellow_range ?? 5,
    status: state?.status ?? 'in_progress',
    guesses: state?.guesses ?? [],
    hints: (state?.hint_attempts ?? []).map((after, i) => ({
      after,
      text: state.hints[i]?.text ?? null,
    })),
    answer,
    search,
    guess,
    giveUp,
  }
}
