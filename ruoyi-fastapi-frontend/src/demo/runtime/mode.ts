import { activeGeneratedScenarioId } from '@/demo/scenarios/generated/active';

export type RuntimeMode = 'real' | 'fallback' | 'demo-offline';
export type LegacyMockMode = 'off' | 'fallback' | 'pure';
export type RuntimeModeSource = 'runtime-mode' | 'legacy-mock';

export interface RuntimeModeEnv {
  VITE_APP_RUNTIME_MODE?: string;
  VITE_ENABLE_MOCK?: string;
  VITE_APP_BASE_API?: string;
  VITE_DEMO_SCENARIO_ID?: string;
  VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS?: string;
  VITE_DEMO_RUNTIME_DEBUG?: string;
}

export interface RuntimeConfig {
  mode: RuntimeMode;
  mockMode: LegacyMockMode;
  apiPrefix: string;
  scenarioId: string;
  allowCandidateScenarios: boolean;
  debug: boolean;
  source: RuntimeModeSource;
}

const DEFAULT_API_PREFIX = '/api';
const DEFAULT_SCENARIO_ID = 'default';
const AUTO_SCENARIO_ID = 'auto';

const LEGACY_MOCK_MODE_MAP: Record<LegacyMockMode, RuntimeMode> = {
  off: 'real',
  fallback: 'fallback',
  pure: 'demo-offline',
};

const RUNTIME_MODE_MOCK_MAP: Record<RuntimeMode, LegacyMockMode> = {
  real: 'off',
  fallback: 'fallback',
  'demo-offline': 'pure',
};

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

function resolveScenarioId(value?: string): string {
  const normalized = normalizeEnvValue(value);

  if (!normalized || normalized === AUTO_SCENARIO_ID) {
    return activeGeneratedScenarioId || DEFAULT_SCENARIO_ID;
  }

  return normalized;
}

export function normalizeLegacyMockMode(value?: string): LegacyMockMode {
  const normalized = normalizeEnvValue(value);
  if (normalized === 'pure' || normalized === 'fallback' || normalized === 'off') {
    return normalized;
  }

  return 'off';
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

export function runtimeModeToMockMode(mode: RuntimeMode): LegacyMockMode {
  return RUNTIME_MODE_MOCK_MAP[mode];
}

export function mockModeToRuntimeMode(mode: LegacyMockMode): RuntimeMode {
  return LEGACY_MOCK_MODE_MAP[mode];
}

export function resolveRuntimeConfig(
  env: RuntimeModeEnv = import.meta.env as unknown as RuntimeModeEnv
): RuntimeConfig {
  const explicitRuntimeMode = normalizeRuntimeMode(env.VITE_APP_RUNTIME_MODE);
  const source: RuntimeModeSource = explicitRuntimeMode ? 'runtime-mode' : 'legacy-mock';
  const mode =
    explicitRuntimeMode ?? mockModeToRuntimeMode(normalizeLegacyMockMode(env.VITE_ENABLE_MOCK));

  return {
    mode,
    mockMode: runtimeModeToMockMode(mode),
    apiPrefix: normalizeApiPrefix(env.VITE_APP_BASE_API),
    scenarioId: resolveScenarioId(env.VITE_DEMO_SCENARIO_ID),
    allowCandidateScenarios: normalizeBoolean(env.VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS),
    debug: normalizeBoolean(env.VITE_DEMO_RUNTIME_DEBUG),
    source,
  };
}

export function isDemoOfflineMode(mode: RuntimeMode): boolean {
  return mode === 'demo-offline';
}

export function isMockRuntimeMode(mode: RuntimeMode): boolean {
  return mode === 'fallback' || mode === 'demo-offline';
}
