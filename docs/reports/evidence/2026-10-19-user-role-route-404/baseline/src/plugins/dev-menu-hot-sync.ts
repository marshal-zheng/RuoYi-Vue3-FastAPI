/* eslint-disable no-console */

import { getDevMenuSignature } from '@/api/system/devMenuSync';
import {
  devMenuSyncMode,
  devMenuSyncPollIntervalMs,
  isDevMenuSyncEnabled,
  isDevMenuSyncPollingEnabled,
  isDevMenuSyncSseEnabled,
} from '@/config/devMenuSync';
import usePermissionStore from '@/store/modules/permission';
import { getToken } from '@/utils/auth';
import { watch, type WatchStopHandle } from 'vue';
import { queryScope } from '@/queries/context';

const AUTH_ERROR_RETRY_DELAY_MS = 60_000;
const MAX_SSE_FAILURES_BEFORE_FALLBACK = 3;
const SSE_RECONNECT_BASE_DELAY_MS = 1000;
const SSE_RECONNECT_MAX_DELAY_MS = 30_000;
const DEV_MENU_SYNC_GLOBAL_KEY = '__DEV_MENU_SYNC__' as const;

const normalizeApiPrefix = (value: string | undefined): string => {
  if (!value) {
    return '/api';
  }
  const normalized = value.trim();
  if (!normalized) {
    return '/api';
  }
  const withLeadingSlash = normalized.startsWith('/') ? normalized : `/${normalized}`;
  return withLeadingSlash.replace(/\/+$/, '') || '/api';
};

const DEV_MENU_EVENTS_URL = `${normalizeApiPrefix(
  import.meta.env.VITE_APP_BASE_API as string | undefined
)}/dev/menu/events`;

let pollTimer: number | null = null;
let reconnectTimer: number | null = null;
let eventSource: EventSource | null = null;
let inFlight = false;
let latestSignature: string | null = null;
let authRetryAfterTs = 0;
let sseFailureCount = 0;
let featureUnavailable = false;
let activeListenersBound = false;
let autoSyncPaused = false;
let connectionGeneration = 0;
let connecting = false;
let stopScopeWatch: WatchStopHandle | undefined;

type DevMenuSyncGlobalApi = {
  refreshRoutes: () => Promise<void>;
  checkSignature: () => Promise<void>;
  enableAutoPolling: () => void;
  disableAutoPolling: () => void;
  enableAutoSync: () => void;
  disableAutoSync: () => void;
};

type SignatureError = {
  response?: {
    status?: number;
    data?: Record<string, unknown>;
  };
  status?: number;
};

type ProbeResult = 'ok' | 'auth' | 'disabled' | 'error' | 'no_token';

declare global {
  interface Window {
    __DEV_MENU_SYNC__?: DevMenuSyncGlobalApi;
  }
}

const isAuthFailure = (error: unknown): boolean => {
  const raw = error as SignatureError;
  const status = raw.response?.status ?? raw.status;
  const errorCode = (raw.response?.data?.errorCode as number | undefined) || undefined;
  return status === 401 || errorCode === 20001 || errorCode === 20002;
};

const isNotFoundFailure = (error: unknown): boolean => {
  const raw = error as SignatureError;
  const status = raw.response?.status ?? raw.status;
  return status === 404;
};

const isDocumentHidden = (): boolean => {
  if (typeof document === 'undefined') {
    return false;
  }
  return document.visibilityState === 'hidden';
};

const isEventSourceSupported = (): boolean => {
  return typeof window !== 'undefined' && typeof window.EventSource === 'function';
};

const isAutoSyncBlocked = (): boolean => {
  return featureUnavailable || autoSyncPaused;
};

const clearReconnectTimer = (): void => {
  if (reconnectTimer !== null && typeof window !== 'undefined') {
    window.clearTimeout(reconnectTimer);
  }
  reconnectTimer = null;
};

const clearPollTimer = (): void => {
  if (pollTimer !== null && typeof window !== 'undefined') {
    window.clearInterval(pollTimer);
  }
  pollTimer = null;
};

const closeEventSource = (): void => {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
};

const unbindActiveListeners = (): void => {
  if (!activeListenersBound) {
    return;
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('focus', onAppActive);
  }
  if (typeof document !== 'undefined') {
    document.removeEventListener('visibilitychange', onVisibilityChange);
  }
  activeListenersBound = false;
};

const stopFallbackPolling = (): void => {
  clearPollTimer();
  inFlight = false;
};

const stopAutomaticSync = (): void => {
  connectionGeneration++;
  connecting = false;
  clearReconnectTimer();
  stopFallbackPolling();
  closeEventSource();
  unbindActiveListeners();
};

function bindActiveListeners(): void {
  if (activeListenersBound || isAutoSyncBlocked()) {
    return;
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('focus', onAppActive);
  }
  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', onVisibilityChange);
  }
  activeListenersBound = true;
}

async function refreshRoutes(reason: string): Promise<void> {
  latestSignature = null;
  const permissionStore = usePermissionStore();
  await permissionStore.reloadDynamicRoutes(reason);
}

function disableFeature(reason: string): void {
  featureUnavailable = true;
  stopAutomaticSync();
  console.info(`[dev-menu-hot-sync] disabled: ${reason}`);
}

function computeReconnectDelay(): number {
  const exponent = Math.max(0, sseFailureCount - 1);
  return Math.min(SSE_RECONNECT_MAX_DELAY_MS, SSE_RECONNECT_BASE_DELAY_MS * 2 ** exponent);
}

function scheduleSseReconnect(delayMs?: number): void {
  if (
    reconnectTimer !== null ||
    isAutoSyncBlocked() ||
    !isDevMenuSyncSseEnabled ||
    !isEventSourceSupported() ||
    !getToken()
  ) {
    return;
  }

  const delay = delayMs ?? computeReconnectDelay();
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    void ensureSseConnection();
  }, delay);
}

async function pollSignature(options: { ignoreVisibility?: boolean } = {}): Promise<void> {
  if (inFlight || isAutoSyncBlocked()) {
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
    authRetryAfterTs = 0;
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
    await refreshRoutes('signature_changed_fallback');
  } catch (error) {
    if (isNotFoundFailure(error)) {
      disableFeature('backend returned 404 for signature fallback');
      return;
    }
    if (isAuthFailure(error)) {
      authRetryAfterTs = Date.now() + AUTH_ERROR_RETRY_DELAY_MS;
      latestSignature = null;
      console.warn('[dev-menu-hot-sync] signature fallback unauthorized, suspend for 60s', error);
      return;
    }
    console.warn('[dev-menu-hot-sync] signature fallback failed, retry next cycle', error);
  } finally {
    inFlight = false;
  }
}

function startFallbackPolling(options: { immediate?: boolean } = {}): void {
  if (isAutoSyncBlocked() || typeof window === 'undefined') {
    return;
  }
  bindActiveListeners();
  if (pollTimer === null) {
    pollTimer = window.setInterval(() => {
      void pollSignature();
    }, devMenuSyncPollIntervalMs);
  }
  if (options.immediate !== false) {
    void pollSignature({ ignoreVisibility: true });
  }
}

async function probeSseAvailability(): Promise<ProbeResult> {
  const generation = connectionGeneration;
  if (!getToken()) {
    latestSignature = null;
    return 'no_token';
  }

  try {
    const payload = await getDevMenuSignature();
    if (generation !== connectionGeneration) return 'no_token';
    authRetryAfterTs = 0;
    if (payload?.signature) {
      latestSignature = payload.signature;
    }
    return 'ok';
  } catch (error) {
    if (generation !== connectionGeneration) return 'no_token';
    if (isNotFoundFailure(error)) {
      disableFeature('backend returned 404 for dev menu sync');
      return 'disabled';
    }
    if (isAuthFailure(error)) {
      authRetryAfterTs = Date.now() + AUTH_ERROR_RETRY_DELAY_MS;
      latestSignature = null;
      scheduleSseReconnect(AUTH_ERROR_RETRY_DELAY_MS);
      console.warn(
        '[dev-menu-hot-sync] SSE unavailable because session is unauthorized, retry in 60s',
        error
      );
      return 'auth';
    }
    return 'error';
  }
}

async function handleSseMenuChanged(event: MessageEvent<string>): Promise<void> {
  try {
    if (event.data) {
      JSON.parse(event.data) as Record<string, unknown>;
    }
  } catch (error) {
    console.warn(
      '[dev-menu-hot-sync] invalid menu_changed payload, force route reload anyway',
      error
    );
  }
  await refreshRoutes('sse_menu_changed');
}

async function handleSseError(): Promise<void> {
  if (!isDevMenuSyncSseEnabled || isAutoSyncBlocked()) {
    return;
  }

  closeEventSource();
  sseFailureCount += 1;

  const probe = await probeSseAvailability();
  if (probe === 'disabled' || probe === 'auth' || probe === 'no_token') {
    return;
  }

  if (sseFailureCount >= MAX_SSE_FAILURES_BEFORE_FALLBACK) {
    startFallbackPolling();
  }
  scheduleSseReconnect();
}

async function ensureSseConnection(options: { immediate?: boolean } = {}): Promise<void> {
  if (
    !isDevMenuSyncSseEnabled ||
    isAutoSyncBlocked() ||
    eventSource !== null ||
    connecting ||
    authRetryAfterTs > Date.now() ||
    !getToken()
  ) {
    return;
  }

  if (!isEventSourceSupported()) {
    console.warn('[dev-menu-hot-sync] EventSource unsupported, fallback to signature polling');
    startFallbackPolling();
    return;
  }

  if (options.immediate) {
    clearReconnectTimer();
  } else if (reconnectTimer !== null) {
    return;
  }

  const generation = connectionGeneration;
  connecting = true;
  const probe = await probeSseAvailability();
  if (generation !== connectionGeneration) return;
  connecting = false;
  if (probe !== 'ok' || isAutoSyncBlocked() || !getToken()) return;
  bindActiveListeners();
  const source = new window.EventSource(DEV_MENU_EVENTS_URL, { withCredentials: true });
  eventSource = source;
  source.addEventListener('open', () => {
    if (source !== eventSource) return;
    sseFailureCount = 0;
    authRetryAfterTs = 0;
    stopFallbackPolling();
  });
  source.addEventListener('menu_changed', (event) => {
    if (source !== eventSource) return;
    void handleSseMenuChanged(event as MessageEvent<string>);
  });
  source.onerror = () => {
    if (source !== eventSource) return;
    void handleSseError();
  };
}

function onAppActive(): void {
  if (isAutoSyncBlocked()) {
    return;
  }
  if (isDevMenuSyncSseEnabled) {
    void ensureSseConnection({ immediate: true });
  }
  if (pollTimer !== null) {
    void pollSignature({ ignoreVisibility: true });
  }
}

function onVisibilityChange(): void {
  if (!isDocumentHidden()) {
    onAppActive();
  }
}

const bindGlobalApi = (): void => {
  if (typeof window === 'undefined') {
    return;
  }
  window[DEV_MENU_SYNC_GLOBAL_KEY] = {
    refreshRoutes: () => refreshRoutes('manual_console_refresh'),
    checkSignature: () => pollSignature({ ignoreVisibility: true }),
    enableAutoPolling: () => startFallbackPolling(),
    disableAutoPolling: () => stopFallbackPolling(),
    enableAutoSync: () => {
      autoSyncPaused = false;
      featureUnavailable = false;
      sseFailureCount = 0;
      if (isDevMenuSyncSseEnabled) {
        void ensureSseConnection({ immediate: true });
        return;
      }
      if (isDevMenuSyncPollingEnabled) {
        startFallbackPolling();
      }
    },
    disableAutoSync: () => {
      autoSyncPaused = true;
      stopAutomaticSync();
    },
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
  sseFailureCount = 0;
  featureUnavailable = false;
  autoSyncPaused = false;

  bindGlobalApi();
  stopScopeWatch?.();
  stopScopeWatch = watch(
    queryScope,
    () => {
      stopAutomaticSync();
      authRetryAfterTs = 0;
      if (!queryScope.value || devMenuSyncMode === 'manual') return;
      if (isDevMenuSyncSseEnabled) void ensureSseConnection({ immediate: true });
      else if (isDevMenuSyncPollingEnabled) startFallbackPolling();
    },
    { flush: 'sync' }
  );

  if (devMenuSyncMode === 'manual') {
    stopAutomaticSync();
    console.info(
      '[dev-menu-hot-sync] manual mode enabled. Use window.__DEV_MENU_SYNC__.refreshRoutes().'
    );
    return;
  }

  if (isDevMenuSyncPollingEnabled) {
    startFallbackPolling();
    console.info(
      '[dev-menu-hot-sync] poll mode enabled, fallback interval:',
      devMenuSyncPollIntervalMs
    );
    return;
  }

  void ensureSseConnection({ immediate: true });
  console.info('[dev-menu-hot-sync] sse mode enabled, listening for /dev/menu/events');
}

export function stopDevMenuHotSync(): void {
  stopScopeWatch?.();
  stopScopeWatch = undefined;
  stopAutomaticSync();
  latestSignature = null;
  authRetryAfterTs = 0;
  sseFailureCount = 0;
  featureUnavailable = false;
  autoSyncPaused = false;
  unbindGlobalApi();
}
