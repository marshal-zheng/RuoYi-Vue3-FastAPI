const ACCESS_TOKEN_SESSION_KEY = 'ruoyi_access_token';
const CSRF_TOKEN_SESSION_KEY = 'ruoyi_csrf_token';
const CSRF_COOKIE_NAME = 'csrf_token';

const resolveSessionStorage = (): Storage | undefined => {
  if (typeof window === 'undefined') {
    return undefined;
  }
  try {
    return window.sessionStorage;
  } catch {
    return undefined;
  }
};

const readSessionValue = (key: string): string => {
  const storage = resolveSessionStorage();
  if (!storage) {
    return '';
  }
  return storage.getItem(key) || '';
};

const readCookieValue = (cookieName: string): string => {
  if (typeof document === 'undefined') {
    return '';
  }
  const pairs = document.cookie ? document.cookie.split(';') : [];
  for (const rawPair of pairs) {
    const pair = rawPair.trim();
    if (!pair) {
      continue;
    }
    const separator = pair.indexOf('=');
    if (separator <= 0) {
      continue;
    }
    const name = pair.slice(0, separator).trim();
    if (name !== cookieName) {
      continue;
    }
    const rawValue = pair.slice(separator + 1);
    try {
      return decodeURIComponent(rawValue);
    } catch {
      return rawValue;
    }
  }
  return '';
};

const writeSessionValue = (key: string, value: string): void => {
  const storage = resolveSessionStorage();
  if (!storage) {
    return;
  }
  if (value) {
    storage.setItem(key, value);
    return;
  }
  storage.removeItem(key);
};

let securityTokenVersion = 0;
let securitySessionVersion = 0;

export const getSecurityTokenVersion = (): number => securityTokenVersion;
export const getSecuritySessionVersion = (): number => securitySessionVersion;

let memoryToken = readSessionValue(ACCESS_TOKEN_SESSION_KEY);
let memoryCsrfToken = readSessionValue(CSRF_TOKEN_SESSION_KEY) || readCookieValue(CSRF_COOKIE_NAME);

export function getToken(): string | undefined {
  return memoryToken || undefined;
}

export function setToken(token: string): string {
  if (memoryToken !== (token || '')) securityTokenVersion++;
  memoryToken = token || '';
  writeSessionValue(ACCESS_TOKEN_SESSION_KEY, memoryToken);
  return memoryToken;
}

export function removeToken(): void {
  securityTokenVersion++;
  securitySessionVersion++;
  memoryToken = '';
  memoryCsrfToken = '';
  writeSessionValue(ACCESS_TOKEN_SESSION_KEY, '');
  writeSessionValue(CSRF_TOKEN_SESSION_KEY, '');
}

export function getCsrfToken(): string | undefined {
  const cookieCsrf = readCookieValue(CSRF_COOKIE_NAME);
  if (cookieCsrf && cookieCsrf !== memoryCsrfToken) {
    memoryCsrfToken = cookieCsrf;
    writeSessionValue(CSRF_TOKEN_SESSION_KEY, memoryCsrfToken);
  }
  return memoryCsrfToken || undefined;
}

export function setCsrfToken(token: string): string {
  memoryCsrfToken = token || '';
  writeSessionValue(CSRF_TOKEN_SESSION_KEY, memoryCsrfToken);
  return memoryCsrfToken;
}

export function clearSecurityTokens(): void {
  securityTokenVersion++;
  securitySessionVersion++;
  memoryToken = '';
  memoryCsrfToken = '';
  writeSessionValue(ACCESS_TOKEN_SESSION_KEY, '');
  writeSessionValue(CSRF_TOKEN_SESSION_KEY, '');
}
