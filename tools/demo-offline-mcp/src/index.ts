#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

import { assertNoProviderApiKeyRequirement, parseServerConfig, type ServerConfig } from './config.js';
import { registerCreateGenerationPlanTool } from './tools/create-generation-plan.js';
import { registerCompileScenarioTool } from './tools/compile-scenario.js';
import { registerActivateRuntimePackageTool } from './tools/activate-runtime-package.js';
import { registerDryRunRuntimePackageTool } from './tools/dry-run-runtime-package.js';
import { registerGenerateDemoTool } from './tools/generate-demo.js';
import { registerGenerateRuntimeDemoTool } from './tools/generate-runtime-demo.js';
import { registerPromoteCandidateTool } from './tools/promote-candidate.js';
import { registerRunChecksTool } from './tools/run-checks.js';
import { registerScanContextTool } from './tools/scan-context.js';
import { registerValidateDraftTool } from './tools/validate-draft.js';
import { registerValidateRuntimePackageTool } from './tools/validate-runtime-package.js';
import { registerWriteCandidateTool } from './tools/write-candidate.js';

export const SERVER_NAME = 'demo-offline-data-mcp';
export const SERVER_VERSION = '0.1.0';

export function createDemoOfflineMcpServer(config: ServerConfig = {}): McpServer {
  assertNoProviderApiKeyRequirement();

  const server = new McpServer({
    name: SERVER_NAME,
    version: SERVER_VERSION,
  });

  registerScanContextTool(server, { repoRoot: config.repoRoot });
  registerGenerateDemoTool(server, { repoRoot: config.repoRoot });
  registerGenerateRuntimeDemoTool(server, { repoRoot: config.repoRoot });
  registerCreateGenerationPlanTool(server, { repoRoot: config.repoRoot });
  registerValidateDraftTool(server, { repoRoot: config.repoRoot });
  registerCompileScenarioTool(server, { repoRoot: config.repoRoot });
  registerWriteCandidateTool(server, { repoRoot: config.repoRoot });
  registerRunChecksTool(server, { repoRoot: config.repoRoot });
  registerPromoteCandidateTool(server, { repoRoot: config.repoRoot });
  registerValidateRuntimePackageTool(server);
  registerDryRunRuntimePackageTool(server);
  registerActivateRuntimePackageTool(server);

  return server;
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  const config = parseServerConfig(argv);
  const server = createDemoOfflineMcpServer(config);
  const transport = new StdioServerTransport();

  console.error(
    `${SERVER_NAME} ${SERVER_VERSION} starting in stdio mode${
      config.repoRoot ? ` for repo ${config.repoRoot}` : ''
    }.`
  );

  await server.connect(transport);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error: unknown) => {
    const message = error instanceof Error ? error.stack || error.message : String(error);
    console.error(message);
    process.exitCode = 1;
  });
}
