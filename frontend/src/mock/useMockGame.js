// Design prototype only: local game state. Stage 4 replaces this hook with
// calls to /api/v1/puzzles/today, keeping the same shape for the components.
import { useMemo, useState } from 'react'
import { SONGS } from './demoSongs.js'
import { compare } from './compare.js'
import { HINT_ATTEMPTS, MAX_ATTEMPTS } from '../game/rules.js'

const EPOCH = Date.UTC(2026, 0, 1)

function todaysSong() {
  const day = Math.floor((Date.now() - EPOCH) / 86_400_000)
  return { number: day + 1, song: SONGS[((day % SONGS.length) + SONGS.length) % SONGS.length] }
}

const normalize = (text) =>
  text.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().trim()

export function useMockGame() {
  const [{ number, song: answer }] = useState(todaysSong)
  const [guesses, setGuesses] = useState([])
  const [gaveUp, setGaveUp] = useState(false)

  const won = guesses.some((g) => g.song.id === answer.id)
  const status = won
    ? 'won'
    : gaveUp
      ? 'gave_up'
      : guesses.length >= MAX_ATTEMPTS
        ? 'lost'
        : 'in_progress'

  const guessedIds = useMemo(() => new Set(guesses.map((g) => g.song.id)), [guesses])

  function search(query) {
    const q = normalize(query)
    if (q.length < 2) return []
    return SONGS.filter(
      (s) =>
        !guessedIds.has(s.id) &&
        [s.title, s.artist, ...s.aliases].some((text) => normalize(text).includes(q)),
    ).slice(0, 10)
  }

  function guess(song) {
    if (status !== 'in_progress' || guessedIds.has(song.id)) return
    setGuesses((prev) => [...prev, { song, tiles: compare(song, answer) }])
  }

  return {
    number,
    answer: status === 'in_progress' ? null : answer,
    guesses,
    status,
    hints: HINT_ATTEMPTS.map((after, i) => ({
      after,
      text: guesses.length >= after || status !== 'in_progress' ? answer.hints[i] : null,
    })),
    search,
    guess,
    giveUp: () => status === 'in_progress' && setGaveUp(true),
  }
}
