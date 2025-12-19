// @ts-nocheck
export function getRequestToken(request: Request): string | undefined {
  const raw = request.headers.get('authorization')
  if (!raw) return undefined
  return raw.replace(/^Bearer\s+/i, '')
}

export async function readJsonBody<T = any>(request: Request): Promise<T | undefined> {
  try {
    return await request.clone().json()
  } catch (error) {
    return undefined
  }
}

export function getSearchParams(request: Request): URLSearchParams {
  const base =
    typeof window === 'undefined'
      ? 'http://localhost'
      : window.location.origin
  const url = request.url.startsWith('http')
    ? new URL(request.url)
    : new URL(request.url, base)
  return url.searchParams
}
