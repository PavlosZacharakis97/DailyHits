import {
  CalendarIcon,
  ChatIcon,
  GlobeIcon,
  HeartIcon,
  MicIcon,
  NoteIcon,
  StyleIcon,
  UserIcon,
} from './Icons.jsx'

/** Display metadata for the 8 tiles, in game order. */
export const TILES = [
  { key: 'artist', label: 'Artist', Icon: UserIcon, tint: 'lav' },
  { key: 'year', label: 'Year', Icon: CalendarIcon, tint: 'mint' },
  { key: 'genre', label: 'Genre', Icon: NoteIcon, tint: 'lav' },
  { key: 'style', label: 'Style', Icon: StyleIcon, tint: 'sky' },
  { key: 'vocal', label: 'Vocal', Icon: MicIcon, tint: 'rose' },
  { key: 'theme', label: 'Theme', Icon: HeartIcon, tint: 'pink' },
  { key: 'country', label: 'Country', Icon: GlobeIcon, tint: 'peach' },
  { key: 'language', label: 'Language', Icon: ChatIcon, tint: 'mint' },
]

export const COLOR_LABEL = { green: 'match', yellow: 'close', gray: 'no match' }

/** Shape marks so colour is never the only signal (colour-blind players). */
export const COLOR_MARK = { green: '✓', yellow: '≈', gray: '✕' }
