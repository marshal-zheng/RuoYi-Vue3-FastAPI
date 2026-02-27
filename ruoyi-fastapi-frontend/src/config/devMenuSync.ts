const DEFAULT_POLL_INTERVAL_MS = 1000;
const MIN_POLL_INTERVAL_MS = 500;
const MAX_POLL_INTERVAL_MS = 10000;

export function parseBooleanEnv(raw: string | undefined): boolean {
  if (!raw) {
    return false;
  }
  const normalized = raw.trim().toLowerCase();
  return ['1', 'true', 'on', 'yes'].includes(normalized);
}

export function normalizePollIntervalMs(raw: string | undefined): number {
  if (!raw) {
    return DEFAULT_POLL_INTERVAL_MS;
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    return DEFAULT_POLL_INTERVAL_MS;
  }
  return Math.min(MAX_POLL_INTERVAL_MS, Math.max(MIN_POLL_INTERVAL_MS, Math.floor(parsed)));
}

export const isDevMenuSyncEnabled =
  import.meta.env.DEV && parseBooleanEnv(import.meta.env.VITE_DEV_MENU_SYNC);

export const devMenuSyncPollIntervalMs = normalizePollIntervalMs(
  import.meta.env.VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS
);
