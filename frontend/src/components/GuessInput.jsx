import { useEffect, useId, useState } from 'react'
import { NoteIcon } from './Icons.jsx'
import styles from './GuessInput.module.css'

/** Autocomplete (WAI-ARIA 1.2 combobox): the player must pick a song from the list. */
export function GuessInput({ onSearch, onGuess, disabled }) {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const [selected, setSelected] = useState(null)
  const [expanded, setExpanded] = useState(false)
  // Message from the last action (selection, empty submit); otherwise the result count.
  const [notice, setNotice] = useState('')
  const id = useId()
  const inputId = `${id}-input`
  const listId = `${id}-list`

  const results = selected ? [] : onSearch(query)
  const open = expanded && results.length > 0
  const optionId = (i) => `${id}-option-${i}`
  const status = notice || suggestionsStatus(query, selected, results.length)

  const activeId = open ? optionId(active) : undefined

  useEffect(() => {
    if (activeId) document.getElementById(activeId)?.scrollIntoView({ block: 'nearest' })
  }, [activeId])

  function choose(song) {
    setSelected(song)
    setQuery(`${song.title} — ${song.artist}`)
    setExpanded(false)
    setNotice(`${song.title} by ${song.artist} selected. Press Enter to guess.`)
  }

  function submit(event) {
    event.preventDefault()
    const song = selected ?? (results.length === 1 ? results[0] : null)
    if (!song) {
      setNotice('Choose a song from the list.')
      setExpanded(true)
      return
    }
    onGuess(song)
    setNotice('')
    setQuery('')
    setSelected(null)
    setActive(0)
  }

  function onKeyDown(event) {
    if (event.key === 'Escape') {
      if (open) setExpanded(false)
      else {
        setQuery('')
        setSelected(null)
      }
      return
    }
    if (!open) {
      if (event.key === 'ArrowDown' && results.length > 0) {
        event.preventDefault()
        setExpanded(true)
      }
      return
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((i) => (i + 1) % results.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((i) => (i - 1 + results.length) % results.length)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      choose(results[active])
    }
  }

  return (
    <form className={styles.form} onSubmit={submit}>
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
          onChange={(e) => {
            setQuery(e.target.value)
            setNotice('')
            setSelected(null)
            setActive(0)
            setExpanded(true)
          }}
          onFocus={() => setExpanded(true)}
          onBlur={() => setExpanded(false)}
          onKeyDown={onKeyDown}
        />
        <button className={styles.submit} type="submit" disabled={disabled}>
          Guess
        </button>
      </div>

      {open && (
        <ul id={listId} className={styles.list} role="listbox" aria-label="Song suggestions">
          {results.map((song, i) => (
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

      <div role="status" aria-live="polite" className="visually-hidden">
        {status}
      </div>
    </form>
  )
}

function suggestionsStatus(query, selected, count) {
  if (selected || query.trim().length < 2) return ''
  if (count === 0) return 'No matching songs.'
  return `${count} ${count === 1 ? 'song' : 'songs'} available. Use up and down arrows, Enter to select.`
}
