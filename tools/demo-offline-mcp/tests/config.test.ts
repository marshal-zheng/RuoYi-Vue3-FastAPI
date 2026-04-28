import { describe, expect, it } from 'vitest';

import { assertNoProviderApiKeyRequirement, parseServerConfig } from '../src/config.js';
import { createDemoOfflineMcpServer, SERVER_NAME, SERVER_VERSION } from '../src/index.js';
import { errorEnvelope, okEnvelope } from '../src/types.js';

describe('demo-offline MCP package skeleton', () => {
  it('parses the optional repository root argument', () => {
    expect(parseServerConfig(['--repo-root', '/workspace/repo'])).toEqual({
      repoRoot: '/workspace/repo',
    });
  });

  it('does not require provider API keys in repository runtime', () => {
    expect(assertNoProviderApiKeyRequirement()).toBe(true);
  });

  it('creates a stdio-capable MCP server instance', () => {
    const server = createDemoOfflineMcpServer();

    expect(server).toBeTruthy();
    expect(SERVER_NAME).toBe('demo-offline-data-mcp');
    expect(SERVER_VERSION).toBe('0.1.0');
  });

  it('uses a stable tool envelope shape', () => {
    expect(okEnvelope('ok', { value: 1 })).toEqual({
      ok: true,
      summary: 'ok',
      data: { value: 1 },
    });

    expect(
      errorEnvelope('failed', [
        {
          path: 'draft.projects[0].name',
          code: 'placeholder_text',
          severity: 'error',
          actual: '测试项目',
          expected: 'industry-specific project name',
          fixHint: 'Replace placeholder content with domain-specific text.',
          autoRepairable: false,
        },
      ])
    ).toMatchObject({
      ok: false,
      summary: 'failed',
      errors: [
        {
          path: 'draft.projects[0].name',
          code: 'placeholder_text',
          autoRepairable: false,
        },
      ],
    });
  });
});
