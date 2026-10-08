import { useEffect, useId, useRef, useState } from 'react'
import { NoteIcon } from './Icons.jsx'
import styles from './GuessInput.module.css'

const DEBOUNCE_MS = 150

/** Autocomplete (WAI-ARIA 1.2 combobox): the player must pick a song from the list. */
export function GuessInput({ onSearch, onGuess, disabled, busy, error, excludeIds }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [active, setActive] = useState(0)
  const [selected, setSelected] = useState(null)
  const [expanded, setExpanded] = useState(false)
  // Message from the last action (selection, empty submit); otherwise the result count.
  const [notice, setNotice] = useState('')
  const pending = useRef({ timer: 0, controller: null })
  const id = useId()
  const inputId = `${id}-input`
  const listId = `${id}-list`

  // Songs already tried this game are not offered again.
  const shown = selected ? [] : results.filter((song) => !excludeIds?.has(song.id))
  const open = expanded && shown.length > 0
  const optionId = (i) => `${id}-option-${i}`
  const activeId = open ? optionId(active) : undefined
  const status = notice || suggestionsStatus(query, selected, shown.length)

  useEffect(() => {
    if (activeId) document.getElementById(activeId)?.scrollIntoView({ block: 'nearest' })
  }, [activeId])

  useEffect(() => () => clearPending(pending.current), [])

  function lookUp(value) {
    clearPending(pending.current)
    if (value.trim().length < 2) {
      setResults([])
      return
    }
    pending.current.timer = setTimeout(() => {
      const controller = new AbortController()
      pending.current.controller = controller
      onSearch(value.trim(), controller.signal).then(
        (songs) => setResults(songs),
        (err) => err.name !== 'AbortError' && setResults([]),
      )
    }, DEBOUNCE_MS)
  }

  function choose(song) {
    setSelected(song)
    setQuery(`${song.title} — ${song.artist}`)
    setExpanded(false)
    setNotice(`${song.title} by ${song.artist} selected. Press Enter to guess.`)
  }

  async function submit(event) {
    event.preventDefault()
    if (busy) return
    const song = selected ?? (shown.length === 1 ? shown[0] : null)
    if (!song) {
      setNotice('Choose a song from the list.')
      setExpanded(true)
      return
    }
    setNotice('')
    setQuery('')
    setSelected(null)
    setResults([])
    setActive(0)
    await onGuess(song)
  }

  function onKeyDown(event) {
    if (event.key === 'Escape') {
      if (open) setExpanded(false)
      else {
        setQuery('')
        setSelected(null)
        setResults([])
      }
      return
    }
    if (!open) {
      if (event.key === 'ArrowDown' && shown.length > 0) {
        event.preventDefault()
        setExpanded(true)
      }
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((i) => (i + 1) % shown.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((i) => (i - 1 + shown.length) % shown.length)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      choose(shown[active])
    }
  }

  return (
    <form className={styles.form} onSubmit={submit} aria-busy={busy || undefined}>
      <div className={styles.field}>
        <NoteIcon className={styles.icon} />
        <label className="visually-hidden" htmlFor={inputId}>
          Your guess
        </label>
        <input
          id={inputId}
          className={styles.input}
          type="text"
          placeholder={disabled ? 'Come back tomorrow for a new song' : 'Type your guess…'}
          autoComplete="off"
          spellCheck="false"
          value={query}
          disabled={disabled}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={open ? listId : undefined}
          aria-activedescendant={activeId}
          aria-describedby={error ? `${id}-error` : undefined}
          onChange={(e) => {
            setQuery(e.target.value)
            setNotice('')
            setSelected(null)
            setActive(0)
            setExpanded(true)
            lookUp(e.target.value)
          }}
          onFocus={() => setExpanded(true)}
          onBlur={() => setExpanded(false)}
          onKeyDown={onKeyDown}
        />
        <button className={styles.submit} type="submit" disabled={disabled || busy}>
          {busy ? '…' : 'Guess'}
        </button>
      </div>

      {open && (
        <ul id={listId} className={styles.list} role="listbox" aria-label="Song suggestions">
          {shown.map((song, i) => (
            <li
              key={song.id}
              id={optionId(i)}
              role="option"
              aria-selected={i === active}
              className={`${styles.option} ${i === active ? styles.optionActive : ''}`}
              onMouseDown={(e) => {
                e.preventDefault()
                choose(song)
              }}
              onMouseEnter={() => setActive(i)}
            >
              <span className={styles.optionTitle}>{song.title}</span>
              <span className={styles.optionArtist}>{song.artist}</span>
            </li>
          ))}
        </ul>
      )}

      {error && (
        <p id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </p>
      )}

      <div role="status" aria-live="polite" className="visually-hidden">
        {status}
      </div>
    </form>
  )
}

function clearPending(pending) {
  clearTimeout(pending.timer)
  pending.controller?.abort()
  pending.controller = null
}

function suggestionsStatus(query, selected, count) {
  if (selected || query.trim().length < 2) return ''
  if (count === 0) return 'No matching songs.'
  return `${count} ${count === 1 ? 'song' : 'songs'} available. Use up and down arrows, Enter to select.`
}
