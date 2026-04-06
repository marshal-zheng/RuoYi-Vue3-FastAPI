const DEFAULT_API_PREFIX = '/api';

function normalizeApiPrefix(value?: string): string {
  if (!value) return DEFAULT_API_PREFIX;
  const withLeadingSlash = value.startsWith('/') ? value : `/${value}`;
  return withLeadingSlash.replace(/\/+$/, '') || DEFAULT_API_PREFIX;
}

export const API_PREFIX = normalizeApiPrefix(
  import.meta.env.VITE_APP_BASE_API as string | undefined
);

export function createApiPath(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_PREFIX}${normalizedPath}`;
}
