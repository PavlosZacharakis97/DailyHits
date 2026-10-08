// The player's cookie choice, kept in a first-party cookie so the server can read it too.
// Bump CONSENT_VERSION when the cookie policy changes to ask everyone again.
const CONSENT_COOKIE = 'dh_consent'
export const CONSENT_VERSION = '1'
const ONE_YEAR = 60 * 60 * 24 * 365

export function readConsent() {
  const match = document.cookie.match(new RegExp(`(?:^|; )${CONSENT_COOKIE}=([^;]*)`))
  return match?.[1] === CONSENT_VERSION
}

export function saveConsent() {
  const secure = location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${CONSENT_COOKIE}=${CONSENT_VERSION}; Max-Age=${ONE_YEAR}; Path=/; SameSite=Lax${secure}`
}

export function clearConsent() {
  document.cookie = `${CONSENT_COOKIE}=; Max-Age=0; Path=/; SameSite=Lax`
}

/** Cookies the site uses, shown in the consent dialog. */
export const COOKIES = [
  {
    name: 'dh_consent',
    purpose: 'Remembers that you accepted cookies.',
    lifetime: '1 year',
  },
  {
    name: 'dh_player',
    purpose:
      'An anonymous random ID so our server can keep today’s guesses and hints. It contains no personal data.',
    lifetime: '1 year',
  },
]
