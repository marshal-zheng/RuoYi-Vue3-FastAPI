import fs from 'node:fs/promises';
import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import { readOfflineStaticContract } from '../offline-static/contract.js';
import { dryRunImportRuntimePackage } from '../offline-static/import-dry-run.js';
import { resolveOfflineStaticTargetPaths } from '../offline-static/paths.js';
import { assertRuntimePackagePointer } from '../offline-static/release-store.js';
import { loadRuntimeReleasePackage } from '../offline-static/writer.js';

export function registerDryRunRuntimePackageTool(server: McpServer): void {
  server.registerTool(
    'demo_offline_dry_run_runtime_package',
    {
      title: 'Dry-run runtime v2 release import',
      description:
        'Assemble an offline-static v2 release package and import it into an isolated fake-indexeddb Dexie database.',
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
        const contractBundle = await readOfflineStaticContract(paths);
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
        const loaded = await loadRuntimeReleasePackage(paths, releaseId, {
          fromStaging: args.fromStaging,
        });
        if (!loaded.scenarioPackage) {
          const envelope = errorEnvelope(
            'Runtime v2 release package could not be assembled for dry-run.',
            loaded.issues.filter((issue) => issue.severity === 'error')
          );
          return {
            isError: true,
            content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
            structuredContent: envelope,
          };
        }
        const envelope = await dryRunImportRuntimePackage(
          contractBundle.contract,
          loaded.scenarioPackage
        );

        return {
          isError: !envelope.ok,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to dry-run runtime v2 release package.', [
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
