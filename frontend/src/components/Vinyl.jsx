import { useId } from 'react'

/** Brand vinyl record (same look as the favicon). Size it with CSS. */
export function Vinyl({ className, label }) {
  const id = useId()
  return (
    <svg className={className} viewBox="0 0 200 200" aria-hidden="true">
      <defs>
        <radialGradient id={`${id}-label`} cx=".35" cy=".3" r=".8">
          <stop offset="0" stopColor="#ffe0bf" />
          <stop offset="1" stopColor="#f7a8a0" />
        </radialGradient>
        <linearGradient id={`${id}-sheen`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#fff" stopOpacity=".35" />
          <stop offset=".5" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="96" fill="#2b2048" />
      {[82, 70, 58].map((r) => (
        <circle key={r} cx="100" cy="100" r={r} fill="none" stroke="#fff" strokeOpacity=".12" strokeWidth="2" />
      ))}
      <circle cx="100" cy="100" r="96" fill={`url(#${id}-sheen)`} />
      <circle cx="100" cy="100" r="34" fill={`url(#${id}-label)`} />
      {label ? (
        <text x="100" y="92" textAnchor="middle" fontSize="15" fontWeight="900" fill="#2b2048" fillOpacity=".55">
          {label}
        </text>
      ) : (
        <path d="M84 96 q8 -10 16 0 t16 0" fill="none" stroke="#2b2048" strokeOpacity=".35" strokeWidth="3" strokeLinecap="round" />
      )}
      <circle cx="100" cy="100" r="6" fill="#2b2048" />
    </svg>
  )
}
