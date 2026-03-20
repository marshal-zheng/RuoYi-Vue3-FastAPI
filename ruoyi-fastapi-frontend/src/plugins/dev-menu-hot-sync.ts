import { getDevMenuSignature } from '@/api/system/devMenuSync';
import {
  devMenuSyncMode,
  devMenuSyncPollIntervalMs,
  isDevMenuSyncEnabled,
  isDevMenuSyncPollingEnabled,
} from '@/config/devMenuSync';
import usePermissionStore from '@/store/modules/permission';
import { getToken } from '@/utils/auth';

let timer: number | null = null;
let inFlight = false;
let latestSignature: string | null = null;
let authRetryAfterTs = 0;
let activeListenersBound = false;

const AUTH_ERROR_RETRY_DELAY_MS = 60_000;
const DEV_MENU_SYNC_GLOBAL_KEY = '__DEV_MENU_SYNC__' as const;

type DevMenuSyncGlobalApi = {
  refreshRoutes: () => Promise<void>;
  checkSignature: () => Promise<void>;
  enableAutoPolling: () => void;
  disableAutoPolling: () => void;
};

declare global {
  interface Window {
    __DEV_MENU_SYNC__?: DevMenuSyncGlobalApi;
  }
}

const isAuthFailure = (error: unknown): boolean => {
  const raw = error as {
    response?: { status?: number; data?: Record<string, unknown> };
    status?: number;
  };
  const status = raw.response?.status ?? raw.status;
  const errorCode = (raw.response?.data?.errorCode as number | undefined) || undefined;
  return status === 401 || errorCode === 20001 || errorCode === 20002;
};

const isDocumentHidden = (): boolean => {
  if (typeof document === 'undefined') {
    return false;
  }
  return document.visibilityState === 'hidden';
};

const pollWhenActive = (): void => {
  if (isDocumentHidden()) {
    return;
  }
  void pollSignature();
};

const onVisibilityChange = (): void => {
  if (!isDocumentHidden()) {
    void pollSignature();
  }
};

const bindActiveListeners = (): void => {
  if (activeListenersBound) {
    return;
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('focus', pollWhenActive);
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', onVisibilityChange);
  }
  activeListenersBound = true;
};

const unbindActiveListeners = (): void => {
  if (!activeListenersBound) {
    return;
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('focus', pollWhenActive);
  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('visibilitychange', onVisibilityChange);
  }
  activeListenersBound = false;
};

interface PollSignatureOptions {
  ignoreVisibility?: boolean;
}

async function pollSignature(options: PollSignatureOptions = {}) {
  if (inFlight) {
    return;
  }
  if (!options.ignoreVisibility && isDocumentHidden()) {
    return;
  }
  if (authRetryAfterTs > Date.now()) {
    return;
  }
  if (!getToken()) {
    latestSignature = null;
    authRetryAfterTs = 0;
    return;
  }
  inFlight = true;
  try {
    const payload = await getDevMenuSignature();
    const nextSignature = payload?.signature;
    if (!nextSignature) {
      return;
    }
    if (!latestSignature) {
      latestSignature = nextSignature;
      return;
    }
    if (latestSignature === nextSignature) {
      return;
    }
    latestSignature = nextSignature;
    const permissionStore = usePermissionStore();
    await permissionStore.reloadDynamicRoutes('signature_changed');
  } catch (error) {
    if (isAuthFailure(error)) {
      authRetryAfterTs = Date.now() + AUTH_ERROR_RETRY_DELAY_MS;
      latestSignature = null;
      console.warn(
        '[dev-menu-hot-sync] signature poll unauthorized, suspend polling for 60s',
        error
      );
      return;
    }
    console.warn('[dev-menu-hot-sync] signature poll failed, retry next cycle', error);
  } finally {
    inFlight = false;
  }
}

async function refreshRoutes(reason: string): Promise<void> {
  latestSignature = null;
  const permissionStore = usePermissionStore();
  await permissionStore.reloadDynamicRoutes(reason);
}

const startPolling = (): void => {
  if (timer !== null) {
    return;
  }
  bindActiveListeners();
  void pollSignature();
  timer = window.setInterval(() => {
    void pollSignature();
  }, devMenuSyncPollIntervalMs);
  console.info('[dev-menu-hot-sync] poll mode enabled, poll interval:', devMenuSyncPollIntervalMs);
};

const stopPolling = (): void => {
  if (timer !== null) {
    window.clearInterval(timer);
    timer = null;
  }
  inFlight = false;
  latestSignature = null;
  authRetryAfterTs = 0;
  unbindActiveListeners();
};

const bindGlobalApi = (): void => {
  if (typeof window === 'undefined') {
    return;
  }
  window[DEV_MENU_SYNC_GLOBAL_KEY] = {
    refreshRoutes: () => refreshRoutes('manual_console_refresh'),
    checkSignature: () => pollSignature({ ignoreVisibility: true }),
    enableAutoPolling: () => startPolling(),
    disableAutoPolling: () => stopPolling(),
  };
};

const unbindGlobalApi = (): void => {
  if (typeof window === 'undefined') {
    return;
  }
  delete window[DEV_MENU_SYNC_GLOBAL_KEY];
};

export function startDevMenuHotSync(): void {
  if (!isDevMenuSyncEnabled) {
    return;
  }
  latestSignature = null;
  authRetryAfterTs = 0;
  bindGlobalApi();
  if (!isDevMenuSyncPollingEnabled) {
    stopPolling();
    console.info(
      `[dev-menu-hot-sync] ${devMenuSyncMode} mode enabled. Use window.__DEV_MENU_SYNC__.refreshRoutes() to refresh menus.`
    );
    return;
  }
  startPolling();
}

export function stopDevMenuHotSync(): void {
  stopPolling();
  unbindGlobalApi();
}
