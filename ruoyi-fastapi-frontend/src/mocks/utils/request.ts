export function getRequestToken(request: Request): string | undefined {
  const raw = request.headers.get('authorization');
  if (!raw) return undefined;
  return raw.replace(/^Bearer\s+/i, '');
}

export async function readJsonBody<T = unknown>(request: Request): Promise<T | undefined> {
  const contentType = request.headers.get('content-type')?.toLowerCase() ?? '';

  if (contentType.includes('application/json')) {
    try {
      return await request.clone().json();
    } catch {
      return undefined;
    }
  }

  if (
    contentType.includes('application/x-www-form-urlencoded') ||
    contentType.includes('multipart/form-data')
  ) {
    try {
      const formData = await request.clone().formData();
      const entries = Array.from(formData.entries());
      if (entries.length > 0) {
        return Object.fromEntries(entries) as T;
      }
    } catch {
      // fallback to text parsing below
    }
  }

  try {
    const text = await request.clone().text();
    const trimmed = text.trim();

    if (!trimmed) {
      return undefined;
    }

    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      return JSON.parse(trimmed) as T;
    }

    if (trimmed.includes('=') || trimmed.includes('&')) {
      return Object.fromEntries(new URLSearchParams(trimmed).entries()) as T;
    }
  } catch {
    return undefined;
  }

  return undefined;
}

export function getSearchParams(request: Request): URLSearchParams {
  const base = typeof window === 'undefined' ? 'http://localhost' : window.location.origin;
  const url = request.url.startsWith('http') ? new URL(request.url) : new URL(request.url, base);
  return url.searchParams;
}
