/** Abstract pastel “cover” for the mystery song (no real artwork is ever shown). */
export function Artwork({ className }) {
  return (
    <svg className={className} viewBox="0 0 320 320" role="img" aria-label="Mystery song cover">
      <rect width="320" height="320" fill="var(--art-sky)" />
      <circle cx="214" cy="112" r="62" fill="var(--art-sun)" opacity="0.85" />
      <path d="M0 170 C60 120 120 150 170 175 S270 215 320 160 V320 H0Z" fill="var(--art-1)" opacity="0.75" />
      <path d="M0 215 C70 180 130 230 200 210 S290 175 320 200 V320 H0Z" fill="var(--art-2)" opacity="0.75" />
      <path d="M0 255 C80 230 140 275 210 255 S290 235 320 250 V320 H0Z" fill="var(--art-3)" opacity="0.75" />
      <path d="M0 290 C90 270 160 305 230 290 S300 278 320 285 V320 H0Z" fill="var(--art-4)" opacity="0.9" />
    </svg>
  )
}
