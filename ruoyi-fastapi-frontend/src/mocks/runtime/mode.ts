import type { MockNetworkStrategy } from '../types';

export type RuntimeMode = 'real' | 'fallback' | 'demo-offline';
export type MockRuntimeMode = 'fallback' | 'demo-offline';
export type RuntimeModeSource = 'runtime-mode' | 'default';

export interface RuntimeModeEnv {
  VITE_APP_RUNTIME_MODE?: string;
  VITE_APP_BASE_API?: string;
  VITE_DEMO_RUNTIME_DEBUG?: string;
}

export interface RuntimeConfig {
  mode: RuntimeMode;
  apiPrefix: string;
  debug: boolean;
  source: RuntimeModeSource;
}

const DEFAULT_API_PREFIX = '/api';

function readCurrentRuntimeEnv(): RuntimeModeEnv {
  return {
    VITE_APP_RUNTIME_MODE: import.meta.env.VITE_APP_RUNTIME_MODE,
    VITE_APP_BASE_API: import.meta.env.VITE_APP_BASE_API,
    VITE_DEMO_RUNTIME_DEBUG: import.meta.env.VITE_DEMO_RUNTIME_DEBUG,
  };
}

function normalizeEnvValue(value?: string): string | undefined {
  const normalized = value?.trim().replace(/^['"]|['"]$/g, '');
  return normalized || undefined;
}

function normalizeApiPrefix(value?: string): string {
  const normalized = normalizeEnvValue(value);
  if (!normalized) return DEFAULT_API_PREFIX;

  const withLeadingSlash = normalized.startsWith('/') ? normalized : `/${normalized}`;
  return withLeadingSlash.replace(/\/+$/, '') || DEFAULT_API_PREFIX;
}

function normalizeBoolean(value?: string, defaultValue = false): boolean {
  const normalized = normalizeEnvValue(value)?.toLowerCase();
  if (normalized === undefined) return defaultValue;

  return ['1', 'true', 'yes', 'on'].includes(normalized);
}

export function normalizeRuntimeMode(value?: string): RuntimeMode | undefined {
  const normalized = normalizeEnvValue(value);
  if (!normalized) return undefined;
  if (normalized === 'real' || normalized === 'fallback' || normalized === 'demo-offline') {
    return normalized;
  }

  throw new Error(
    `Unsupported VITE_APP_RUNTIME_MODE "${normalized}". Expected real, fallback, or demo-offline.`
  );
}

export function resolveRuntimeConfig(env: RuntimeModeEnv = readCurrentRuntimeEnv()): RuntimeConfig {
  const explicitRuntimeMode = normalizeRuntimeMode(env.VITE_APP_RUNTIME_MODE);

  return {
    mode: explicitRuntimeMode ?? 'real',
    apiPrefix: normalizeApiPrefix(env.VITE_APP_BASE_API),
    debug: normalizeBoolean(env.VITE_DEMO_RUNTIME_DEBUG),
    source: explicitRuntimeMode ? 'runtime-mode' : 'default',
  };
}

export function isDemoOfflineMode(mode: RuntimeMode): boolean {
  return mode === 'demo-offline';
}

export function isMockRuntimeMode(mode: RuntimeMode): mode is MockRuntimeMode {
  return mode === 'fallback' || mode === 'demo-offline';
}

export function strategyForRuntimeMode(mode: MockRuntimeMode): MockNetworkStrategy {
  return mode === 'demo-offline' ? 'pure' : 'fallback';
}
