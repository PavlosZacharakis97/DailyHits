import { useEffect, useRef, useState } from 'react'
import { knowledge } from '../game/knowledge.js'
import { nextPuzzleAt } from '../game/stats.js'
import { useCountdown } from '../hooks/useCountdown.js'
import { Artwork } from './Artwork.jsx'
import { Vinyl } from './Vinyl.jsx'
import { GuessInput } from './GuessInput.jsx'
import { BulbIcon, FlagIcon, LockIcon, NoteIcon, PlayIcon } from './Icons.jsx'
import { COLOR_LABEL, TILES } from './tiles.js'
import { WinCelebration } from './WinCelebration.jsx'
import styles from './PuzzleCard.module.css'

const STATUS_TITLE = {
  won: 'You got it!',
  lost: 'Out of guesses',
  gave_up: 'Here is the answer',
}

export function PuzzleCard({ game, onShowResult }) {
  const { number, answer, guesses, status, hints, maxAttempts } = game
  const finished = status !== 'in_progress'
  const known = knowledge(guesses, game.yearYellowRange)
  const announcement = announcementFor(game, maxAttempts)
  const titleRef = useRef(null)

  useEffect(() => {
    // The input is disabled at game end, so move focus to the result.
    if (finished) titleRef.current?.focus()
  }, [finished])

  return (
    <section className={styles.card} aria-labelledby="puzzle-title">
      <div className={styles.layout}>
        <div className={styles.side}>
          <div className={styles.cover} data-won={status === 'won' || undefined}>
            {status === 'won' ? (
              <WinCelebration />
            ) : (
              <Sleeve spinning={!finished} />
            )}
          </div>
          <Extras hints={hints} finished={finished} onGiveUp={game.giveUp} />
        </div>

        <div className={styles.main}>
          <div className={styles.head}>
            <div className={styles.titleRow}>
              <h1 id="puzzle-title" ref={titleRef} tabIndex={-1} className={`${styles.title} gradient-text`} data-won={status === 'won' || undefined}>
                {finished ? STATUS_TITLE[status] : 'Guess the song'}
              </h1>
              <NextSong number={number} date={game.date} />
            </div>

            {finished && !answer && <p className={styles.answerArtist}>Loading the answer…</p>}
            {finished && answer ? (
              <div className={styles.answer}>
                <p className={styles.answerTitle}>{answer.title}</p>
                <p className={styles.answerArtist}>
                  {answer.artist}
                  {answer.featured.length > 0 && ` feat. ${answer.featured.join(', ')}`} · {answer.year}
                </p>
                <a
                  className={styles.youtube}
                  href={answer.youtube_url}
                  target="_blank"
                  rel="noopener"
                >
                  <PlayIcon size={14} /> Watch on YouTube
                  <span className="visually-hidden"> (opens in a new tab)</span>
                </a>
              </div>
            ) : finished ? null : (
              <p className={styles.mystery}>
                <span aria-hidden="true">????</span>
                <span className="visually-hidden">Unknown song</span>
              </p>
            )}

            <Progress used={guesses.length} max={maxAttempts} hintAt={hints.map((h) => h.after)} status={status} />
            {finished && answer && (
              <button type="button" className={styles.resultsButton} onClick={onShowResult}>
                Results &amp; share
              </button>
            )}
          </div>

          <ul className={styles.grid} role="list" aria-label="What you know about the song">
            {TILES.map(({ key, label, Icon, tint }) => {
              const fact = known[key]
              return (
                <li key={key} className={styles.tile} data-state={fact?.color ?? 'unknown'}>
                  <span className={styles.icon} data-tint={tint}>
                    <Icon size={20} />
                  </span>
                  <span className={styles.tileText}>
                    <span className={styles.tileLabel}>{label}</span>
                    {fact ? (
                      <span className={styles.tileValue}>
                        {fact.color === 'yellow' && <span aria-hidden="true">≈ </span>}
                        {fact.value}
                        {fact.color !== 'range' && (
                          <span className="visually-hidden">, {COLOR_LABEL[fact.color]}</span>
                        )}
                      </span>
                    ) : (
                      <span className={styles.tileValue}>
                        <span aria-hidden="true">—</span>
                        <span className="visually-hidden">not known yet</span>
                      </span>
                    )}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      </div>

      <GuessInput
        onSearch={game.search}
        onGuess={game.guess}
        disabled={finished}
        busy={game.busy}
        error={game.actionError}
        excludeIds={new Set(guesses.map((g) => g.song.id))}
      />

      <div role="status" aria-live="polite" aria-atomic="true" className="visually-hidden">
        {announcement}
      </div>
    </section>
  )
}

/** Issue number and a live countdown to the next daily song. */
function NextSong({ number, date }) {
  const countdown = useCountdown(nextPuzzleAt(date))
  if (countdown.done) {
    return (
      <button type="button" className={`${styles.badge} ${styles.badgeNew}`} onClick={() => window.location.reload()}>
        <NoteIcon size={16} /> New song! Play
      </button>
    )
  }
  return (
    <span className={styles.badge}>
      <NoteIcon size={16} /> #{number}
      <span className={styles.badgeDivider} aria-hidden="true">·</span>
      <span>
        New song in{' '}
        <time className={styles.countdown} aria-label={countdown.spoken}>
          {countdown.text}
        </time>
      </span>
    </span>
  )
}

/** Album sleeve with the record peeking out and spinning while the game is on. */
function Sleeve({ spinning }) {
  return (
    <div className={styles.sleeve} data-spinning={spinning || undefined}>
      <Vinyl className={styles.sleeveRecord} />
      <Artwork className={styles.art} />
    </div>
  )
}

/** Progress as a track scrubber: one segment per guess, hint unlocks marked. */
function Progress({ used, max, hintAt, status }) {
  const left = max - used
  const summary =
    status === 'won'
      ? `Solved in ${used} of ${max}`
      : status === 'in_progress'
        ? `${left} ${left === 1 ? 'try' : 'tries'} left`
        : `${used} of ${max} guesses used`
  return (
    <div className={styles.progress}>
      <div
        className={styles.track}
        role="progressbar"
        aria-label="Guesses used"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={used}
        aria-valuetext={summary}
        style={{ '--done': used / max }}
      >
        {Array.from({ length: max }, (_, i) => (
          <span
            key={i}
            className={styles.segment}
            data-used={i < used || undefined}
            data-hint={hintAt.includes(i + 1) || undefined}
          />
        ))}
        <span className={styles.playhead} aria-hidden="true" />
      </div>
      <span className={styles.left}>{summary}</span>
    </div>
  )
}

function Extras({ hints, finished, onGiveUp }) {
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    if (!confirming) return undefined
    const timer = setTimeout(() => setConfirming(false), 4000)
    return () => clearTimeout(timer)
  }, [confirming])

  return (
    <div className={styles.extras}>
      {hints.map((hint, i) =>
        hint.text ? (
          <div key={hint.after} className={styles.hint} data-tint={i === 0 ? 'mint' : 'peach'}>
            <span className={styles.hintLabel}>
              <BulbIcon size={16} /> Hint {i + 1}
            </span>
            <p className={styles.hintText}>{hint.text}</p>
          </div>
        ) : (
          <div key={hint.after} className={styles.extra}>
            <span className={styles.extraIcon} data-tint={i === 0 ? 'mint' : 'peach'}>
              <LockIcon size={20} />
            </span>
            <span className={styles.extraText}>
              Hint {i + 1}
              <span className={styles.extraSub}>after guess {hint.after}</span>
            </span>
          </div>
        ),
      )}
      {!finished && (
        <button
          type="button"
          className={`${styles.extra} ${styles.giveUp}`}
          data-confirming={confirming || undefined}
          onClick={() => (confirming ? onGiveUp() : setConfirming(true))}
        >
          <span className={styles.extraIcon} data-tint="pink">
            <FlagIcon size={20} />
          </span>
          <span className={styles.extraText}>
            {confirming ? 'Sure?' : 'Give up'}
            <span className={styles.extraSub}>{confirming ? 'tap again' : 'show answer'}</span>
          </span>
        </button>
      )}
    </div>
  )
}

/** Text for the polite live region: last guess, unlocked hint or the result. */
function announcementFor({ guesses, status, answer, hints }, maxAttempts) {
  const count = guesses.length
  if (status !== 'in_progress') {
    if (!answer) return ''
    const by = `${answer.title} by ${answer.artist}`
    if (status === 'won') return `You got it! The song is ${by}, solved in ${count} of ${maxAttempts}.`
    if (status === 'lost') return `Out of guesses. The answer was ${by}.`
    return `You gave up. The answer was ${by}.`
  }
  if (count === 0) return ''
  // Every message names the guess number, so consecutive messages always differ.
  const { song, tiles } = guesses[count - 1]
  const n = (c) => tiles.filter((t) => t.color === c).length
  const left = maxAttempts - count
  let text = `Guess ${count} of ${maxAttempts}: ${song.title} by ${song.artist}. ${n('green')} match, ${n('yellow')} close, ${n('gray')} no match. ${left} ${left === 1 ? 'try' : 'tries'} left.`
  const unlocked = hints.findIndex((h) => h.after === count)
  if (unlocked >= 0) text += ` Hint ${unlocked + 1} unlocked: ${hints[unlocked].text}`
  return text
}
