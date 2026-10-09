// Per-browser results of daily games, for streaks and the stats screen.
// Moves to the server with accounts; until then it lives in localStorage.

const KEY = 'dh_stats'
const DAY_MS = 86_400_000

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '{}') ?? {}
  } catch {
    return {}
  }
}

/** Remember how today's game ended (idempotent per date). */
export function recordResult({ date, status, attempts }) {
  if (!date || status === 'in_progress') return
  const results = load()
  if (results[date]?.status === status && results[date]?.attempts === attempts) return
  results[date] = { status, attempts }
  try {
    localStorage.setItem(KEY, JSON.stringify(results))
  } catch {
    // Storage disabled: stats simply are not kept.
  }
}

/** Points for one game: 11 − attempts when won, 0 otherwise (same rule as the leaderboard). */
export function pointsFor(status, attempts) {
  return status === 'won' ? Math.max(0, 11 - attempts) : 0
}

export function computeStats(today, maxAttempts = 10) {
  const results = load()
  const dates = Object.keys(results).sort()
  const won = (d) => results[d]?.status === 'won'

  const distribution = Array.from({ length: maxAttempts }, () => 0)
  let maxStreak = 0
  let run = 0
  let previous = null
  for (const date of dates) {
    const r = results[date]
    if (r.status === 'won' && r.attempts >= 1 && r.attempts <= maxAttempts) {
      distribution[r.attempts - 1] += 1
    }
    const consecutive = previous && Date.parse(date) - Date.parse(previous) === DAY_MS
    run = won(date) ? (consecutive && won(previous) ? run + 1 : 1) : 0
    maxStreak = Math.max(maxStreak, run)
    previous = date
  }

  // The current streak survives until today's game is lost or a day is skipped.
  let current = 0
  let cursor = won(today) ? today : shift(today, -1)
  while (won(cursor)) {
    current += 1
    cursor = shift(cursor, -1)
  }

  const played = dates.length
  const wins = dates.filter(won).length
  return {
    played,
    wins,
    winRate: played ? Math.round((wins / played) * 100) : 0,
    currentStreak: current,
    maxStreak,
    distribution,
    points: dates.reduce((sum, d) => sum + pointsFor(results[d].status, results[d].attempts), 0),
  }
}

function shift(isoDate, days) {
  return new Date(Date.parse(isoDate) + days * DAY_MS).toISOString().slice(0, 10)
}

const SQUARE = { green: '🟩', yellow: '🟨', gray: '⬜' }

/** Spoiler-free result for sharing: one row of squares per guess. */
export function shareText({ number, status, guesses, maxAttempts }) {
  const score = status === 'won' ? `${guesses.length}/${maxAttempts}` : `X/${maxAttempts}`
  const rows = guesses.map((g) => g.tiles.map((t) => SQUARE[t.color]).join(''))
  return [`dailyhit #${number} ${score} 🎵`, ...rows, window.location.origin].join('\n')
}

/** Timestamp of the next puzzle: midnight UTC after `date`. */
export function nextPuzzleAt(date) {
  return Date.parse(date) + DAY_MS
}
