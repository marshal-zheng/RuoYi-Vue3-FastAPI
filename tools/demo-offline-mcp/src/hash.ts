import crypto from 'node:crypto';

import type { CompiledDemoScenarioPackage } from './types.js';

export function canonicalJson(value: unknown): string {
  if (value === null) return 'null';

  if (typeof value === 'string' || typeof value === 'boolean') {
    return JSON.stringify(value);
  }

  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw new Error('Cannot canonicalize non-finite numbers.');
    }

    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    return `[${value.map((item) => (item === undefined ? 'null' : canonicalJson(item))).join(',')}]`;
  }

  if (value && typeof value === 'object' && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record)
      .filter((key) => record[key] !== undefined)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key])}`)
      .join(',')}}`;
  }

  if (value === undefined) return 'null';

  throw new Error(`Cannot canonicalize value of type "${typeof value}".`);
}

export function sha256Hex(value: string): string {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

export function sha256CanonicalJson(value: unknown): string {
  return sha256Hex(canonicalJson(value));
}

export function createScenarioFingerprintInput(scenarioPackage: CompiledDemoScenarioPackage): unknown {
  const cloned = JSON.parse(JSON.stringify(scenarioPackage)) as CompiledDemoScenarioPackage & {
    scenario: Partial<CompiledDemoScenarioPackage['scenario']>;
  };
  const scenario = cloned.scenario as Partial<CompiledDemoScenarioPackage['scenario']>;
  delete scenario.fingerprint;
  return cloned;
}

export function computeScenarioFingerprint(scenarioPackage: CompiledDemoScenarioPackage): string {
  return sha256CanonicalJson(createScenarioFingerprintInput(scenarioPackage));
}

export function computePackageSha256(scenarioPackage: CompiledDemoScenarioPackage): string {
  return sha256CanonicalJson(scenarioPackage);
}
