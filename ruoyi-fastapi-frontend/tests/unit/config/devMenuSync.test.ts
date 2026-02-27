import { describe, it, expect } from 'vitest';
import { parseBooleanEnv, normalizePollIntervalMs } from '@/config/devMenuSync';

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

  it('normalizes polling interval with sane defaults', () => {
    expect(normalizePollIntervalMs(undefined)).toBe(1000);
    expect(normalizePollIntervalMs('2000')).toBe(2000);
    expect(normalizePollIntervalMs('100')).toBe(500);
    expect(normalizePollIntervalMs('100000')).toBe(10000);
    expect(normalizePollIntervalMs('not-a-number')).toBe(1000);
  });
});
