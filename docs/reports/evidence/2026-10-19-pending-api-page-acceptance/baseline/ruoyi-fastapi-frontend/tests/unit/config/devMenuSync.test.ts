import { describe, expect, it } from 'vitest';

import {
  normalizeDevMenuSyncMode,
  normalizePollIntervalMs,
  parseBooleanEnv,
} from '@/config/devMenuSync';

describe('dev menu sync env helpers', () => {
  it('parses boolean values from env strings', () => {
    expect(parseBooleanEnv('1')).toBe(true);
    expect(parseBooleanEnv('true')).toBe(true);
    expect(parseBooleanEnv('on')).toBe(true);
    expect(parseBooleanEnv('yes')).toBe(true);
    expect(parseBooleanEnv('0')).toBe(false);
    expect(parseBooleanEnv('false')).toBe(false);
    expect(parseBooleanEnv(undefined)).toBe(false);
  });

  it('normalizes fallback polling interval with sane defaults', () => {
    expect(normalizePollIntervalMs(undefined)).toBe(30000);
    expect(normalizePollIntervalMs('7000')).toBe(7000);
    expect(normalizePollIntervalMs('100')).toBe(5000);
    expect(normalizePollIntervalMs('999999')).toBe(120000);
    expect(normalizePollIntervalMs('not-a-number')).toBe(30000);
  });

  it('defaults sync mode to sse while keeping manual and poll compatibility', () => {
    expect(normalizeDevMenuSyncMode(undefined)).toBe('sse');
    expect(normalizeDevMenuSyncMode('manual')).toBe('manual');
    expect(normalizeDevMenuSyncMode('poll')).toBe('poll');
    expect(normalizeDevMenuSyncMode('unexpected')).toBe('sse');
  });
});
