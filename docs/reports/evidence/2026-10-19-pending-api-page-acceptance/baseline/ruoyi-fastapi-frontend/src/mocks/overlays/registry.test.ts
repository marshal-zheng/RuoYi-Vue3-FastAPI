import Ajv2020 from 'ajv/dist/2020';
import { describe, expect, it } from 'vitest';

import registrySchema from './registry.schema.json';
import {
  listMockOverlaySummaries,
  loadMockOverlayRegistry,
  validateMockOverlayRegistryEntries,
} from './index';
import type { MockOverlayRegistryEntry } from './types';

const ajv = new Ajv2020({ allErrors: true, strict: false });
const validate = ajv.compile(registrySchema);

function schemaErrors() {
  return (validate.errors ?? [])
    .map((error) => {
      const property =
        error.keyword === 'additionalProperties'
          ? ` ${String(error.params.additionalProperty)}`
          : '';
      return `${error.instancePath || '/'} ${error.message ?? 'schema error'}${property}`;
    })
    .join('; ');
}

function baseEntry(overrides: Partial<MockOverlayRegistryEntry> = {}): MockOverlayRegistryEntry {
  return {
    id: 'fixture-overlay',
    name: 'Fixture Overlay',
    stateType: 'empty',
    target: {
      method: 'GET',
      openapiPath: '/fixture',
      mswPath: '/api/fixture',
      handlerTag: 'fixture:list',
    },
    pages: ['fixture-page'],
    owner: 'fixture',
    tests: ['ruoyi-fastapi-frontend/src/mocks/overlays/registry.test.ts'],
    risk: 'Fixture risk.',
    coreMatrix: false,
    e2eEnabled: false,
    resetStrategy: 'overlay-only',
    composition: {},
    response: {
      projection: 'empty-page',
    },
    ...overrides,
  };
}

describe('mock overlay registry', () => {
  it('loads committed overlay registry entries in a stable summary order', () => {
    const entries = loadMockOverlayRegistry();
    const summaries = listMockOverlaySummaries(entries);

    expect(entries.length).toBeGreaterThanOrEqual(8);
    expect(entries.map((entry) => entry.id)).toContain('project-list-empty');
    expect(summaries[0]).toEqual(
      expect.objectContaining({
        id: 'project-create-500',
        coreMatrix: true,
        method: 'POST',
        openapiPath: '/project',
        handlerTag: 'project:create',
      })
    );
    expect(summaries).toEqual(
      [...summaries].sort(
        (left, right) =>
          Number(right.coreMatrix) - Number(left.coreMatrix) ||
          left.openapiPath.localeCompare(right.openapiPath) ||
          left.method.localeCompare(right.method) ||
          left.id.localeCompare(right.id)
      )
    );
  });

  it('keeps committed registry documents valid against registry.schema.json', () => {
    const documents = [
      loadMockOverlayRegistry().filter((entry) => entry.owner === 'project'),
      loadMockOverlayRegistry().filter((entry) => entry.owner === 'project-version'),
      loadMockOverlayRegistry().filter((entry) => entry.owner === 'topology'),
      loadMockOverlayRegistry().filter((entry) => entry.owner === 'simulation'),
    ];

    for (const document of documents) {
      expect(validate(document), schemaErrors()).toBe(true);
    }
  });

  it('rejects duplicate overlay ids', () => {
    const entry = baseEntry();
    expect(() => validateMockOverlayRegistryEntries([entry, { ...entry }])).toThrow(
      /Duplicate mock overlay id: fixture-overlay/
    );
  });

  it('rejects missing required fields with schema validation', () => {
    const invalidEntry = baseEntry() as Partial<MockOverlayRegistryEntry>;
    delete invalidEntry.owner;

    expect(validate([invalidEntry])).toBe(false);
    expect(schemaErrors()).toContain("must have required property 'owner'");
  });

  it('rejects additional registry properties with schema validation', () => {
    const invalidEntry = {
      ...baseEntry(),
      leakedToken: 'should-not-appear',
    };

    expect(validate([invalidEntry])).toBe(false);
    expect(schemaErrors()).toContain('must NOT have additional properties leakedToken');
  });
});
