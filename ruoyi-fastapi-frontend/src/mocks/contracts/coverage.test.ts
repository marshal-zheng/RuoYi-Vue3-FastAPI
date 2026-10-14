import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  buildMockContractReport,
  enumerateOpenApiOperations,
  fingerprintOpenApi,
  pathPatternsMatch,
} from '../../../scripts/mock-contracts-core.mjs';

function writeFixtureFile(root: string, relativePath: string, content: string) {
  const file = join(root, relativePath);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, content);
}

function createContractFixture(options: {
  registryExtra?: Record<string, unknown>;
  handlerTag?: string;
}) {
  const repoRoot = mkdtempSync(join(tmpdir(), 'mock-contract-fixture-'));
  const frontendRoot = join(repoRoot, 'ruoyi-fastapi-frontend');
  const registryExtra = options.registryExtra ?? {};
  const handlerTag = options.handlerTag ?? 'demo:handler';
  const registrySchema = readFileSync(
    resolve(process.cwd(), 'src/mocks/contracts/coverage/registry.schema.json'),
    'utf8'
  );

  writeFixtureFile(frontendRoot, 'package.json', '{"private":true}');
  writeFixtureFile(
    frontendRoot,
    'src/mocks/contracts/coverage/registry.schema.json',
    registrySchema
  );
  writeFixtureFile(frontendRoot, 'src/mocks/handlers/demo.test.ts', 'export {};');
  writeFixtureFile(
    frontendRoot,
    'src/mocks/handlers/demo.ts',
    `import { http, HttpResponse } from 'msw';
import { createApiPath } from '../constants';
import { withBackendFallback } from '../utils/with-backend-fallback';

export function createDemoHandlers(strategy) {
  return [
    http.get(createApiPath('/demo'), ({ request }) =>
      withBackendFallback(request, () => HttpResponse.json({ ok: true }), {
        strategy,
        tag: '${handlerTag}',
      })
    ),
  ];
}
`
  );
  writeFixtureFile(
    repoRoot,
    'shared/openapi.json',
    JSON.stringify({
      openapi: '3.1.0',
      info: { title: 'Fixture', version: '1.0.0' },
      paths: {
        '/demo': {
          get: {
            operationId: 'getDemo',
            tags: ['demo'],
            responses: {
              200: {
                content: {
                  'application/json': {
                    schema: {
                      type: 'object',
                      properties: { ok: { type: 'boolean' } },
                    },
                  },
                },
              },
            },
          },
        },
      },
    })
  );
  writeFixtureFile(
    frontendRoot,
    'src/mocks/contracts/coverage/registry/demo.json',
    JSON.stringify([
      {
        method: 'GET',
        openapiPath: '/demo',
        mswPath: '/api/demo',
        handlerTag: 'demo:handler',
        owner: 'demo',
        status: 'mock-handled',
        critical: true,
        schemaStatus: 'openapi-validated',
        tests: ['ruoyi-fastapi-frontend/src/mocks/handlers/demo.test.ts'],
        persistence: 'readonly',
        ...registryExtra,
      },
    ])
  );

  return frontendRoot;
}

describe('mock contract coverage registry', () => {
  it('enumerates OpenAPI operations and schema availability from fixtures', () => {
    const fixture = {
      openapi: '3.1.0',
      info: { title: 'Fixture', version: '1.0.0' },
      paths: {
        '/empty': {
          post: {
            operationId: 'createEmpty',
            tags: ['fixture'],
            summary: 'Create Empty',
            responses: {
              200: {
                content: {
                  'application/json': {
                    schema: {},
                  },
                },
              },
            },
          },
        },
        '/items/{item_id}': {
          get: {
            operationId: 'getItem',
            tags: ['fixture'],
            summary: 'Get Item',
            responses: {
              200: {
                content: {
                  'application/json': {
                    schema: {
                      type: 'object',
                      properties: {
                        id: { type: 'integer' },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    };

    expect(enumerateOpenApiOperations(fixture)).toEqual([
      expect.objectContaining({
        method: 'POST',
        openapiPath: '/empty',
        operationId: 'createEmpty',
        responseSchemaAvailability: 'empty',
      }),
      expect.objectContaining({
        method: 'GET',
        openapiPath: '/items/{item_id}',
        operationId: 'getItem',
        responseSchemaAvailability: 'available',
      }),
    ]);
    expect(fingerprintOpenApi(fixture)).toHaveLength(64);
  });

  it('matches OpenAPI and MSW path params by position instead of param names', () => {
    expect(pathPatternsMatch('/project/{project_id}', '/api/project/:projectId')).toBe(true);
    expect(pathPatternsMatch('/project/{project_id}/topology', '/api/project/:id/topology')).toBe(
      true
    );
    expect(pathPatternsMatch('/project/{project_id}/topology', '/api/project/topology/:id')).toBe(
      false
    );
  });

  it('keeps the committed registry aligned with shared/openapi.json', () => {
    const report = buildMockContractReport({ cwd: process.cwd() });
    expect(report.artifact.path).toBe('shared/openapi.json');
    expect(report.artifact.operationCount).toBe(244);
    expect(report.entries).toHaveLength(report.artifact.operationCount);
    expect(report.summary.byStatus['mock-handled']).toBeGreaterThan(0);
    expect(report.summary.byStatus.missing).toBeGreaterThan(0);
    expect(report.summary.criticalTotal).toBeGreaterThan(0);
    expect(report.failures).toEqual([]);
  });

  it('keeps real-only, missing, unsupported, and binary classifications explicit', () => {
    const report = buildMockContractReport({ cwd: process.cwd() });

    const realOnlyEntries = report.entries.filter(
      (entry: { status: string }) => entry.status === 'real-only'
    );
    expect(realOnlyEntries.length).toBeGreaterThan(0);
    realOnlyEntries.forEach(
      (entry: { critical: boolean; reason?: string; migrationTarget?: string }) => {
        expect(entry.critical).toBe(false);
        expect(entry.reason).toBeTruthy();
        expect(entry.migrationTarget).toBeTruthy();
      }
    );

    const missingEntries = report.entries.filter(
      (entry: { status: string }) => entry.status === 'missing'
    );
    expect(missingEntries.length).toBeGreaterThan(0);
    missingEntries.forEach(
      (entry: {
        critical: boolean;
        owner?: string;
        reason?: string;
        impact?: string;
        migrationTarget?: string;
      }) => {
        expect(entry.critical).toBe(false);
        expect(entry.owner).toBeTruthy();
        expect(entry.reason).toBeTruthy();
        expect(entry.impact).toBeTruthy();
        expect(entry.migrationTarget).toBeTruthy();
      }
    );

    const unsupportedEntries = report.entries.filter(
      (entry: { status: string }) => entry.status === 'unsupported-501'
    );
    expect(unsupportedEntries).toHaveLength(35);
    expect(unsupportedEntries).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          handlerTag: 'simulation:session-start-unsupported',
          persistence: 'unsupported-501',
        }),
      ])
    );
    expect(
      report.entries.filter(
        (entry: { schemaStatus: string }) => entry.schemaStatus === 'binary-response'
      ).length
    ).toBeGreaterThan(0);
  });

  it('rejects registry properties that are not allowed by registry.schema.json', () => {
    const frontendRoot = createContractFixture({
      registryExtra: { leakedToken: 'should-not-appear-in-report' },
    });

    expect(() => buildMockContractReport({ cwd: frontendRoot })).toThrow(
      /does not match registry\.schema\.json: .*unknown property leakedToken/
    );
  });

  it('fails when registry handler tags do not match the runtime handler for the endpoint', () => {
    const frontendRoot = createContractFixture({ handlerTag: 'demo:actual' });
    const report = buildMockContractReport({ cwd: frontendRoot });

    expect(report.failures).toEqual([
      expect.objectContaining({
        code: 'handler-tag-mismatch',
        method: 'GET',
        openapiPath: '/demo',
        handlerTag: 'demo:handler',
      }),
    ]);
  });
});
