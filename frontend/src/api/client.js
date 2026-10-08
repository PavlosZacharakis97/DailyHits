// Thin JSON client for the game API (/api is proxied to Django in dev).

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

async function request(method, path, { body, signal } = {}) {
  let response
  try {
    response = await fetch(`/api/v1${path}`, {
      method,
      signal,
      credentials: 'same-origin',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError(0, 'network', 'No connection. Check your internet and try again.')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const err = data?.error ?? {}
    throw new ApiError(response.status, err.code ?? 'server_error', err.message ?? 'Something went wrong.', err.details)
  }
  return data
}

const query = (params) => new URLSearchParams(params).toString()

export const api = {
  puzzle: (day, edition) => request('GET', `/puzzles/${day}?${query({ edition })}`),
  guess: (day, edition, songId) =>
    request('POST', `/puzzles/${day}/guess?${query({ edition })}`, { body: { song_id: songId } }),
  giveUp: (day, edition) => request('POST', `/puzzles/${day}/give-up?${query({ edition })}`),
  reveal: (day, edition) => request('GET', `/puzzles/${day}/reveal?${query({ edition })}`),
  search: (q, edition, signal) => request('GET', `/songs/search?${query({ q, edition })}`, { signal }),
}
