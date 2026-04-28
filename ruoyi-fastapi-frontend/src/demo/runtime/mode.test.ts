import { describe, expect, it } from 'vitest';
import { activeGeneratedScenarioId } from '@/demo/scenarios/generated/active';

import {
  mockModeToRuntimeMode,
  normalizeRuntimeMode,
  resolveRuntimeConfig,
  runtimeModeToMockMode,
} from './mode';

describe('runtime mode resolver', () => {
  it('uses VITE_APP_RUNTIME_MODE before legacy mock mode', () => {
    expect(
      resolveRuntimeConfig({
        VITE_APP_RUNTIME_MODE: 'demo-offline',
        VITE_ENABLE_MOCK: 'fallback',
        VITE_APP_BASE_API: '/api',
      })
    ).toMatchObject({
      mode: 'demo-offline',
      mockMode: 'pure',
      source: 'runtime-mode',
    });
  });

  it('maps legacy VITE_ENABLE_MOCK values when runtime mode is absent', () => {
    expect(resolveRuntimeConfig({ VITE_ENABLE_MOCK: 'off' }).mode).toBe('real');
    expect(resolveRuntimeConfig({ VITE_ENABLE_MOCK: 'fallback' }).mode).toBe('fallback');
    expect(resolveRuntimeConfig({ VITE_ENABLE_MOCK: 'pure' }).mode).toBe('demo-offline');
  });

  it('normalizes API prefix and scenario id', () => {
    expect(
      resolveRuntimeConfig({
        VITE_APP_RUNTIME_MODE: "'fallback'",
        VITE_APP_BASE_API: 'dev-api/',
        VITE_DEMO_SCENARIO_ID: '"customer-a"',
        VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS: 'true',
      })
    ).toMatchObject({
      mode: 'fallback',
      apiPrefix: '/dev-api',
      scenarioId: 'customer-a',
      allowCandidateScenarios: true,
    });
  });

  it('uses the active generated scenario when scenario id is auto or absent', () => {
    const expectedScenarioId = activeGeneratedScenarioId || 'default';

    expect(resolveRuntimeConfig({ VITE_APP_RUNTIME_MODE: 'demo-offline' }).scenarioId).toBe(
      expectedScenarioId
    );
    expect(
      resolveRuntimeConfig({
        VITE_APP_RUNTIME_MODE: 'demo-offline',
        VITE_DEMO_SCENARIO_ID: 'auto',
      }).scenarioId
    ).toBe(expectedScenarioId);
    expect(
      resolveRuntimeConfig({
        VITE_APP_RUNTIME_MODE: 'demo-offline',
        VITE_DEMO_SCENARIO_ID: 'default',
      }).scenarioId
    ).toBe('default');
  });

  it('rejects invalid explicit runtime modes', () => {
    expect(() => normalizeRuntimeMode('mock')).toThrow('Unsupported VITE_APP_RUNTIME_MODE "mock"');
  });

  it('keeps runtime and legacy mock mappings explicit', () => {
    expect(runtimeModeToMockMode('real')).toBe('off');
    expect(runtimeModeToMockMode('fallback')).toBe('fallback');
    expect(runtimeModeToMockMode('demo-offline')).toBe('pure');

    expect(mockModeToRuntimeMode('off')).toBe('real');
    expect(mockModeToRuntimeMode('fallback')).toBe('fallback');
    expect(mockModeToRuntimeMode('pure')).toBe('demo-offline');
  });

  it('keeps real and fallback runtime semantics independent from candidate scenario loading', () => {
    expect(
      resolveRuntimeConfig({
        VITE_APP_RUNTIME_MODE: 'real',
        VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS: 'true',
      })
    ).toMatchObject({
      mode: 'real',
      mockMode: 'off',
      allowCandidateScenarios: true,
    });
    expect(resolveRuntimeConfig({ VITE_APP_RUNTIME_MODE: 'fallback' })).toMatchObject({
      mode: 'fallback',
      mockMode: 'fallback',
      allowCandidateScenarios: false,
    });
  });
});
