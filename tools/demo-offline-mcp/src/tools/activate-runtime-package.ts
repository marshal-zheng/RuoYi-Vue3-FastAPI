import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import { resolveOfflineStaticTargetPaths } from '../offline-static/paths.js';
import { activateRuntimePackage } from '../offline-static/writer.js';

export function registerActivateRuntimePackageTool(server: McpServer): void {
  server.registerTool(
    'demo_offline_activate_runtime_package',
    {
      title: 'Activate runtime scenario package',
      description:
        'Validate a staged v2 release and atomically activate it by switching active.pointer.json in an offline-static package.',
      inputSchema: {
        targetRoot: z.string().min(1),
        packageFormat: z.literal('v2').optional(),
        releaseId: z.string().optional(),
        confirm: z.literal(true),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: true,
        idempotentHint: false,
        openWorldHint: false,
      },
    },
    async (args) => {
      try {
        const paths = await resolveOfflineStaticTargetPaths({ targetRoot: args.targetRoot });
        const envelope = await activateRuntimePackage(paths, { releaseId: args.releaseId });

        return {
          isError: !envelope.ok,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to activate runtime package.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
