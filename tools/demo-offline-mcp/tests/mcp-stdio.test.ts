import path from 'node:path';

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { afterEach, describe, expect, it } from 'vitest';

const repoRoot = path.resolve(import.meta.dirname, '../../..');
const packageRoot = path.resolve(import.meta.dirname, '..');
const tsxBin = path.join(packageRoot, 'node_modules', '.bin', 'tsx');

let client: Client | undefined;
let transport: StdioClientTransport | undefined;

describe('Demo Offline MCP stdio server', () => {
  afterEach(async () => {
    await client?.close();
    await transport?.close();
    client = undefined;
    transport = undefined;
  });

  it('lists registered tools and calls scan_context over stdio', async () => {
    client = new Client({
      name: 'demo-offline-mcp-test-client',
      version: '0.1.0',
    });
    transport = new StdioClientTransport({
      command: tsxBin,
      args: ['src/index.ts', '--repo-root', repoRoot],
      cwd: packageRoot,
      env: {
        DEMO_OFFLINE_MCP_AUDIT: 'off',
      },
      stderr: 'pipe',
    });

    await client.connect(transport);
    const tools = await client.listTools();
    const toolNames = tools.tools.map((tool) => tool.name).sort();

    expect(toolNames).toEqual([
      'demo_offline_compile_scenario',
      'demo_offline_create_generation_plan',
      'demo_offline_promote_candidate',
      'demo_offline_run_checks',
      'demo_offline_scan_context',
      'demo_offline_validate_draft',
      'demo_offline_write_candidate',
    ]);
    expect(tools.tools.find((tool) => tool.name === 'demo_offline_scan_context')).toMatchObject({
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    });
    expect(tools.tools.find((tool) => tool.name === 'demo_offline_promote_candidate')).toMatchObject({
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
      },
    });

    const scanResult = await client.callTool({
      name: 'demo_offline_scan_context',
      arguments: {
        includeGenerated: true,
        includeCandidates: true,
        responseFormat: 'json',
      },
    });

    expect(scanResult.structuredContent).toMatchObject({
      ok: true,
      data: {
        safeSlices: ['project', 'simulation'],
        copiedSlices: ['auth', 'system'],
      },
    });
  }, 15000);
});
