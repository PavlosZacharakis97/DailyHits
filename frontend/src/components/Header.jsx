import { useTheme } from '../hooks/useTheme.js'
import { ChartIcon, HelpIcon, MoonIcon, SunIcon } from './Icons.jsx'
import styles from './Header.module.css'

export function Header({ onHelp, onStats }) {
  const [theme, toggleTheme] = useTheme()
  const dark = theme === 'dark'

  return (
    <header className={styles.header}>
      <a className={styles.logo} href="/" aria-label="dailyhit home">
        <img className={styles.mark} src="/brand/favicon-music.svg" alt="" width="44" height="44" />
        <span className={`${styles.word} gradient-text`}>dailyhit</span>
      </a>
      <nav className={styles.actions} aria-label="Game menu">
        {onHelp && (
          <button type="button" className={styles.iconButton} onClick={onHelp} aria-label="How to play">
            <HelpIcon size={20} />
          </button>
        )}
        {onStats && (
          <button type="button" className={styles.iconButton} onClick={onStats} aria-label="Your stats">
            <ChartIcon size={20} />
          </button>
        )}
        <button
          type="button"
          className={styles.iconButton}
          onClick={toggleTheme}
          aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {dark ? <SunIcon size={20} /> : <MoonIcon size={20} />}
        </button>
      </nav>
    </header>
  )
}
