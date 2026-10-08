import { YEAR_YELLOW_RANGE } from './rules.js'

/**
 * What the player has learnt about the answer, derived only from the tiles the
 * server returned for past guesses (never from the answer itself).
 *
 * Returns { [key]: { color: 'green' | 'yellow' | 'range', value } }; missing keys are unknown.
 */
export function knowledge(guesses) {
  const known = {}
  for (const { tiles } of guesses) {
    for (const tile of tiles) {
      if (tile.key === 'year') continue
      if (tile.color === 'green') known[tile.key] = { color: 'green', value: tile.value }
      else if (tile.color === 'yellow' && known[tile.key]?.color !== 'green') {
        known[tile.key] = { color: 'yellow', value: tile.value }
      }
    }
  }
  const year = yearKnowledge(guesses.map((g) => g.tiles.find((t) => t.key === 'year')))
  if (year) known.year = year
  return known
}

function yearKnowledge(tiles) {
  let low = -Infinity
  let high = Infinity
  let close = false
  for (const tile of tiles) {
    const year = Number(tile.value)
    if (tile.color === 'green') return { color: 'green', value: tile.value }
    const near = tile.color === 'yellow'
    close ||= near
    if (tile.direction === 'up') {
      low = Math.max(low, year + (near ? 1 : YEAR_YELLOW_RANGE + 1))
      if (near) high = Math.min(high, year + YEAR_YELLOW_RANGE)
    } else {
      high = Math.min(high, year - (near ? 1 : YEAR_YELLOW_RANGE + 1))
      if (near) low = Math.max(low, year - YEAR_YELLOW_RANGE)
    }
  }
  if (low === -Infinity && high === Infinity) return null
  const value =
    low === high
      ? String(low)
      : low === -Infinity
        ? `${high} or earlier`
        : high === Infinity
          ? `${low} or later`
          : `${low}–${high}`
  return { color: close ? 'yellow' : 'range', value }
}
