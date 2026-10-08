import { useEffect, useState } from 'react'

function readTheme() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

/** Light/dark theme, initialised in index.html before first paint. */
export function useTheme() {
  const [theme, setTheme] = useState(readTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      localStorage.setItem('theme', theme)
    } catch {
      // Storage can be unavailable (private mode); the theme still works for this visit.
    }
  }, [theme])

  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))]
}
