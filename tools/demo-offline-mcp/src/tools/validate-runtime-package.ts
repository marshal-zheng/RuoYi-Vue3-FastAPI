import fs from 'node:fs/promises';
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import { resolveOfflineStaticTargetPaths } from '../offline-static/paths.js';
import { assertRuntimePackagePointer } from '../offline-static/release-store.js';
import { validateRuntimeRelease } from '../offline-static/writer.js';

export function registerValidateRuntimePackageTool(server: McpServer): void {
  server.registerTool(
    'demo_offline_validate_runtime_package',
    {
      title: 'Validate runtime v2 release package',
      description:
        'Validate an offline-static v2 Release Store package from active/previous pointer, releaseId, or staging releaseId.',
      inputSchema: {
        targetRoot: z.string().min(1),
        packageFormat: z.literal('v2').optional(),
        releaseId: z.string().optional(),
        pointer: z.enum(['active', 'previous']).optional().default('active'),
        fromStaging: z.boolean().optional().default(false),
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
        const paths = await resolveOfflineStaticTargetPaths({ targetRoot: args.targetRoot });
        const releaseId =
          args.releaseId ??
          assertRuntimePackagePointer(
            JSON.parse(
              await fs.readFile(
                args.pointer === 'previous' ? paths.previousPointerPath : paths.activePointerPath,
                'utf8'
              )
            )
          ).releaseId;
        const envelope = await validateRuntimeRelease(paths, releaseId, {
          fromStaging: args.fromStaging,
        });

        return {
          isError: !envelope.ok,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to validate runtime v2 release package.', [
          issueFromUnknown(error),
        ]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
