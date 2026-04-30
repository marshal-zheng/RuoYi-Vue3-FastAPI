import { demoScenarioJsonSchema } from './scenario-json-schema';
import {
  createDemoOfflineContractManifestDraft,
  type DemoOfflineContractManifest,
  type DemoOfflineContractManifestDraft,
} from './contract';
import {
  createDemoDomcAdapterReferences,
  createDemoDomcModuleContractFingerprints,
  createDemoDomcRegistry,
  type DemoDomcRegistry,
} from '../domc';
import type { DemoScenarioPackage } from './schema';

const REMOTE_REF_PATTERN = /^[a-z][a-z0-9+.-]*:\/\//i;
const ABSOLUTE_FILE_PATH_PATTERN =
  /^(?:[A-Za-z]:[\\/]|\\\\|\/(?:Users|home|var|tmp|private|etc|Volumes|opt|usr|root)\b)/;
const SENSITIVE_VALUE_PATTERN =
  /(sk-[a-z0-9]{16,}|akia[0-9a-z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)/i;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === '[object Object]';
}

export function canonicalJson(value: unknown): string {
  if (value === null) {
    return 'null';
  }

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

  if (isPlainObject(value)) {
    return `{${Object.keys(value)
      .filter((key) => value[key] !== undefined)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(',')}}`;
  }

  if (value === undefined) {
    return 'null';
  }

  throw new Error(`Cannot canonicalize value of type "${typeof value}".`);
}

export async function sha256Hex(text: string): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error('Web Crypto SHA-256 support is required.');
  }

  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

export async function sha256CanonicalJson(value: unknown): Promise<string> {
  return sha256Hex(canonicalJson(value));
}

export function createScenarioFingerprintInput(scenarioPackage: DemoScenarioPackage): unknown {
  const scenarioWithoutFingerprint: Partial<DemoScenarioPackage['scenario']> = {
    ...scenarioPackage.scenario,
  };
  delete scenarioWithoutFingerprint.fingerprint;

  return {
    ...scenarioPackage,
    scenario: scenarioWithoutFingerprint,
  };
}

export async function computeDemoScenarioFingerprint(
  scenarioPackage: DemoScenarioPackage
): Promise<string> {
  return sha256CanonicalJson(createScenarioFingerprintInput(scenarioPackage));
}

export async function computePackageSha256(scenarioPackage: DemoScenarioPackage): Promise<string> {
  return sha256CanonicalJson(scenarioPackage);
}

export function createContractFingerprintInput(
  contract: DemoOfflineContractManifest | DemoOfflineContractManifestDraft,
  scenarioSchema: unknown = demoScenarioJsonSchema
): unknown {
  const stableContract: Partial<DemoOfflineContractManifestDraft> = { ...contract };
  delete stableContract.contractFingerprint;
  delete stableContract.generatedAt;

  return {
    contract: stableContract,
    scenarioSchema,
  };
}

export async function computeContractFingerprint(
  contract: DemoOfflineContractManifest | DemoOfflineContractManifestDraft,
  scenarioSchema: unknown = demoScenarioJsonSchema
): Promise<string> {
  return sha256CanonicalJson(createContractFingerprintInput(contract, scenarioSchema));
}

export async function createDemoOfflineContractManifest(
  generatedAt?: string,
  options: { domcRegistry?: DemoDomcRegistry } = {}
): Promise<DemoOfflineContractManifest> {
  const registry = options.domcRegistry ?? (await createDemoDomcRegistry(generatedAt));
  const moduleContractFingerprints = await createDemoDomcModuleContractFingerprints(registry);
  const draft = createDemoOfflineContractManifestDraft(generatedAt, {
    domcRegistry: registry,
    moduleContractFingerprints,
    adapterReferences: createDemoDomcAdapterReferences(registry),
  });
  assertDemoContractExportSafe(draft);
  assertDemoContractExportSafe(demoScenarioJsonSchema);
  assertDemoContractExportSafe(registry);

  return {
    ...draft,
    contractFingerprint: await computeContractFingerprint(draft, demoScenarioJsonSchema),
  };
}

export function assertDemoContractExportSafe(value: unknown, path = '$'): void {
  if (typeof value === 'string') {
    if (ABSOLUTE_FILE_PATH_PATTERN.test(value)) {
      throw new Error(
        `Unsafe demo contract export at ${path}: absolute filesystem paths are not allowed.`
      );
    }

    if (SENSITIVE_VALUE_PATTERN.test(value)) {
      throw new Error(
        `Unsafe demo contract export at ${path}: secret-like values are not allowed.`
      );
    }

    return;
  }

  if (!value || typeof value !== 'object') {
    return;
  }

  if (Array.isArray(value)) {
    value.forEach((item, index) => assertDemoContractExportSafe(item, `${path}[${index}]`));
    return;
  }

  Object.entries(value as Record<string, unknown>).forEach(([key, child]) => {
    const childPath = `${path}.${key}`;
    if (key === '$ref' && typeof child === 'string' && REMOTE_REF_PATTERN.test(child)) {
      throw new Error(`Unsafe demo contract export at ${childPath}: remote $ref is not allowed.`);
    }

    assertDemoContractExportSafe(child, childPath);
  });
}
