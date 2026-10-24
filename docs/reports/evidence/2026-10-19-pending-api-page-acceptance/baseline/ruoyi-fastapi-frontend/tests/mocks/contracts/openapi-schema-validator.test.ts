import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { validateOpenApiResponse } from './openapi-schema-validator';

function writeFixtureOpenApi(document: unknown): string {
  const directory = mkdtempSync(join(tmpdir(), 'mock-contract-openapi-'));
  const file = join(directory, 'openapi.json');
  writeFileSync(file, JSON.stringify(document));
  return file;
}

describe('openapi-schema-validator', () => {
  it('validates response bodies against dereferenced component schemas', () => {
    const openApiPath = writeFixtureOpenApi({
      openapi: '3.1.0',
      paths: {
        '/demo/{id}': {
          get: {
            responses: {
              200: {
                content: {
                  'application/json': {
                    schema: {
                      $ref: '#/components/schemas/DemoResponse',
                    },
                  },
                },
              },
            },
          },
        },
      },
      components: {
        schemas: {
          DemoResponse: {
            type: 'object',
            required: ['id'],
            properties: {
              id: { type: 'integer' },
            },
          },
        },
      },
    });

    expect(
      validateOpenApiResponse({
        method: 'GET',
        openapiPath: '/demo/{id}',
        body: { id: 1 },
        openApiPath,
      })
    ).toEqual({ ok: true });
  });

  it('returns field-level validation failures', () => {
    const openApiPath = writeFixtureOpenApi({
      openapi: '3.1.0',
      paths: {
        '/demo': {
          get: {
            responses: {
              200: {
                content: {
                  'application/json': {
                    schema: {
                      type: 'object',
                      required: ['name'],
                      properties: {
                        name: { type: 'string' },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    });

    const result = validateOpenApiResponse({
      method: 'GET',
      openapiPath: '/demo',
      body: {},
      openApiPath,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toEqual([
      expect.objectContaining({
        keyword: 'required',
      }),
    ]);
  });

  it('skips empty, missing, and non-json response schemas with explicit reasons', () => {
    const openApiPath = writeFixtureOpenApi({
      openapi: '3.1.0',
      paths: {
        '/empty': {
          get: {
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
        '/missing': {
          get: {
            responses: {
              204: {},
            },
          },
        },
        '/download': {
          get: {
            responses: {
              200: {
                content: {
                  'application/octet-stream': {},
                },
              },
            },
          },
        },
      },
    });

    for (const openapiPath of ['/empty', '/missing', '/download']) {
      const result = validateOpenApiResponse({
        method: 'GET',
        openapiPath,
        body: {},
        openApiPath,
      });
      expect(result.ok).toBe(true);
      expect(result.skipped).toBe(true);
      expect(result.reason).toBeTruthy();
    }
  });
});
