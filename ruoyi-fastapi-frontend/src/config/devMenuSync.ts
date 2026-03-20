const DEFAULT_POLL_INTERVAL_MS = 30000;
const MIN_POLL_INTERVAL_MS = 5000;
const MAX_POLL_INTERVAL_MS = 120000;
const DEFAULT_SYNC_MODE = 'poll';

export type DevMenuSyncMode = 'poll' | 'manual';

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

export function normalizeDevMenuSyncMode(raw: string | undefined): DevMenuSyncMode {
  if (!raw) {
    return DEFAULT_SYNC_MODE;
  }
  const normalized = raw.trim().toLowerCase();
  if (normalized === 'manual') {
    return 'manual';
  }
  return 'poll';
}

export const isDevMenuSyncEnabled =
  import.meta.env.DEV && parseBooleanEnv(import.meta.env.VITE_DEV_MENU_SYNC);

export const devMenuSyncMode = normalizeDevMenuSyncMode(import.meta.env.VITE_DEV_MENU_SYNC_MODE);
export const isDevMenuSyncPollingEnabled = isDevMenuSyncEnabled && devMenuSyncMode === 'poll';

export const devMenuSyncPollIntervalMs = normalizePollIntervalMs(
  import.meta.env.VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS
);
