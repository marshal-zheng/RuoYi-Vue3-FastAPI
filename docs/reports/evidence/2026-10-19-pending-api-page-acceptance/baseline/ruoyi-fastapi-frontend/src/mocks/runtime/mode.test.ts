import { describe, expect, it } from 'vitest';

import {
  isDemoOfflineMode,
  isMockRuntimeMode,
  normalizeRuntimeMode,
  resolveRuntimeConfig,
  strategyForRuntimeMode,
  type RuntimeModeEnv,
} from './mode';

describe('mock runtime mode', () => {
  it('defaults to real mode without legacy fallback variables', () => {
    const legacyEnv = {
      [`VITE_${'ENABLE_MOCK'}`]: 'pure',
      [`VITE_DEMO_${'SCENARIO_ID'}`]: 'auto',
      [`VITE_DEMO_${'ALLOW_CANDIDATE_SCENARIOS'}`]: 'true',
    } as unknown as RuntimeModeEnv;

    expect(resolveRuntimeConfig(legacyEnv)).toEqual({
      mode: 'real',
      apiPrefix: '/api',
      debug: false,
      source: 'default',
    });
  });

  it('normalizes explicit runtime mode, API prefix, and debug flag', () => {
    expect(
      resolveRuntimeConfig({
        VITE_APP_RUNTIME_MODE: '"demo-offline"',
        VITE_APP_BASE_API: 'admin-api/',
        VITE_DEMO_RUNTIME_DEBUG: 'yes',
      })
    ).toEqual({
      mode: 'demo-offline',
      apiPrefix: '/admin-api',
      debug: true,
      source: 'runtime-mode',
    });
  });

  it('rejects unsupported runtime mode values', () => {
    expect(() => normalizeRuntimeMode('pure')).toThrow(
      'Unsupported VITE_APP_RUNTIME_MODE "pure". Expected real, fallback, or demo-offline.'
    );
  });

  it('maps mock runtime modes to network strategies', () => {
    expect(isMockRuntimeMode('real')).toBe(false);
    expect(isMockRuntimeMode('fallback')).toBe(true);
    expect(isDemoOfflineMode('demo-offline')).toBe(true);
    expect(strategyForRuntimeMode('fallback')).toBe('fallback');
    expect(strategyForRuntimeMode('demo-offline')).toBe('pure');
  });
});
