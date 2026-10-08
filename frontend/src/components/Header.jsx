import { useTheme } from '../hooks/useTheme.js'
import { MoonIcon, SunIcon } from './Icons.jsx'
import styles from './Header.module.css'

export function Header() {
  const [theme, toggleTheme] = useTheme()
  const dark = theme === 'dark'

  return (
    <header className={styles.header}>
      <a className={styles.logo} href="/" aria-label="dailyhit home">
        <img className={styles.mark} src="/brand/favicon-music.svg" alt="" width="44" height="44" />
        <span className={`${styles.word} gradient-text`}>dailyhit</span>
      </a>
      <button
        type="button"
        className={styles.themeToggle}
        onClick={toggleTheme}
        aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      >
        {dark ? <SunIcon size={20} /> : <MoonIcon size={20} />}
      </button>
    </header>
  )
}
