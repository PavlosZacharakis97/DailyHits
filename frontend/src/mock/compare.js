// Design prototype only: in the real game the server compares guesses (stage 3)
// and the answer never reaches the browser before the game ends.
import { RELATED_GENRES, STYLE_GENRE, THEME_GROUP } from './demoSongs.js'

const YEAR_YELLOW_RANGE = 5

const intersects = (a, b) => a.some((x) => b.includes(x))

const VOCAL_LABELS = { male: 'Male', female: 'Female', mixed: 'Mixed', instrumental: 'Instrumental' }

export const TILE_KEYS = ['artist', 'year', 'genre', 'style', 'vocal', 'theme', 'country', 'language']

export function tileValue(song, key) {
  switch (key) {
    case 'artist':
      return song.artist
    case 'style':
      return song.styles.join(', ')
    case 'vocal':
      return VOCAL_LABELS[song.vocal]
    case 'theme':
      return song.themes[0]
    default:
      return String(song[key])
  }
}

function artistColor(guess, answer) {
  if (guess.artist === answer.artist) return 'green'
  const guessAll = [guess.artist, ...guess.featured]
  const answerAll = [answer.artist, ...answer.featured]
  if (intersects(guessAll, answerAll) || intersects(guess.members, answer.members)) return 'yellow'
  return 'gray'
}

function yearTile(guess, answer) {
  if (guess.year === answer.year) return { color: 'green' }
  return {
    color: Math.abs(guess.year - answer.year) <= YEAR_YELLOW_RANGE ? 'yellow' : 'gray',
    direction: answer.year > guess.year ? 'up' : 'down',
  }
}

const COLOR = {
  artist: artistColor,
  genre: (g, a) =>
    g.genre === a.genre ? 'green' : RELATED_GENRES[a.genre].includes(g.genre) ? 'yellow' : 'gray',
  style: (g, a) => {
    if (intersects(g.styles, a.styles)) return 'green'
    const answerGenres = a.styles.map((s) => STYLE_GENRE[s])
    return g.styles.some((s) => answerGenres.includes(STYLE_GENRE[s])) ? 'yellow' : 'gray'
  },
  vocal: (g, a) => (g.vocal === a.vocal ? 'green' : 'gray'),
  theme: (g, a) => {
    if (intersects(g.themes, a.themes)) return 'green'
    const answerGroups = a.themes.map((t) => THEME_GROUP[t])
    return g.themes.some((t) => answerGroups.includes(THEME_GROUP[t])) ? 'yellow' : 'gray'
  },
  country: (g, a) => (g.country === a.country ? 'green' : g.region === a.region ? 'yellow' : 'gray'),
  language: (g, a) => (g.language === a.language ? 'green' : 'gray'),
}

export function compare(guess, answer) {
  return TILE_KEYS.map((key) => ({
    key,
    value: tileValue(guess, key),
    ...(key === 'year' ? yearTile(guess, answer) : { color: COLOR[key](guess, answer) }),
  }))
}
