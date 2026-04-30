import type { DemoDomcModuleContract, DemoDomcRegistry, DemoDomcRegistryDraft } from './types';

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === '[object Object]';
}

export function canonicalDomcJson(value: unknown): string {
  if (value === null) return 'null';
  if (typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw new Error('Cannot canonicalize non-finite DOMC number.');
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => (item === undefined ? 'null' : canonicalDomcJson(item))).join(',')}]`;
  }
  if (isPlainObject(value)) {
    return `{${Object.keys(value)
      .filter((key) => value[key] !== undefined)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalDomcJson(value[key])}`)
      .join(',')}}`;
  }
  if (value === undefined) return 'null';
  throw new Error(`Cannot canonicalize DOMC value of type "${typeof value}".`);
}

async function sha256Hex(text: string): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error('Web Crypto SHA-256 support is required for DOMC fingerprints.');
  }
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

export function createDomcRegistryFingerprintInput(
  registry: DemoDomcRegistry | DemoDomcRegistryDraft
): unknown {
  const stableRegistry: Partial<DemoDomcRegistryDraft> = { ...registry };
  delete stableRegistry.generatedAt;
  delete stableRegistry.domcFingerprint;
  return stableRegistry;
}

export async function computeDomcRegistryFingerprint(
  registry: DemoDomcRegistry | DemoDomcRegistryDraft
): Promise<string> {
  return sha256Hex(canonicalDomcJson(createDomcRegistryFingerprintInput(registry)));
}

export async function computeDomcModuleFingerprint(
  moduleContract: DemoDomcModuleContract
): Promise<string> {
  return sha256Hex(canonicalDomcJson(moduleContract));
}

export async function computeDomcModuleFingerprints(
  registry: DemoDomcRegistry | DemoDomcRegistryDraft
): Promise<Record<string, string>> {
  const entries = await Promise.all(
    registry.modules.map(async (moduleContract) => [
      moduleContract.moduleId,
      await computeDomcModuleFingerprint(moduleContract),
    ])
  );
  return Object.fromEntries(entries);
}
