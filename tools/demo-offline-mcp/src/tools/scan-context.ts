import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { scanDemoOfflineContext, formatDemoOfflineContext } from '../demo-scan.js';
import { issueFromUnknown } from '../errors.js';
import { withToolAudit } from '../audit-log.js';
import { errorEnvelope } from '../types.js';

export interface RegisterScanContextToolOptions {
  repoRoot?: string;
}

export function registerScanContextTool(
  server: McpServer,
  options: RegisterScanContextToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_scan_context',
    {
      title: 'Scan demo-offline context',
      description:
        'Scan the repository demo-offline schema, scenarios, handlers, scripts, and generated scenario state.',
      inputSchema: {
        includeGenerated: z.boolean().optional().default(true),
        includeCandidates: z.boolean().optional().default(true),
        responseFormat: z.enum(['json', 'markdown']).optional().default('json'),
      },
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (args) => {
      try {
        const envelope = await withToolAudit(
          'demo_offline_scan_context',
          {
            repoRoot: options.repoRoot,
            input: {
              includeGenerated: args.includeGenerated,
              includeCandidates: args.includeCandidates,
              responseFormat: args.responseFormat,
            },
          },
          (paths) =>
            scanDemoOfflineContext(paths, {
              includeGenerated: args.includeGenerated,
              includeCandidates: args.includeCandidates,
            })
        );
        const text =
          args.responseFormat === 'markdown' && envelope.data
            ? formatDemoOfflineContext(envelope.data)
            : JSON.stringify(envelope, null, 2);

        return {
          content: [{ type: 'text', text }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to scan demo-offline context.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
