import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { summarizeDraft, summarizePlan, withToolAudit } from '../audit-log.js';
import { scanDemoOfflineContext } from '../demo-scan.js';
import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import { validateIndustryDataDraft } from '../validator.js';

export interface RegisterValidateDraftToolOptions {
  repoRoot?: string;
}

export function registerValidateDraftTool(
  server: McpServer,
  options: RegisterValidateDraftToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_validate_draft',
    {
      title: 'Validate IndustryDataDraft',
      description:
        'Validate an AI-authored IndustryDataDraft and return structured repair guidance without writing files.',
      inputSchema: {
        plan: z.record(z.unknown()),
        draft: z.record(z.unknown()),
        autoRepair: z.boolean().optional().default(false),
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
          'demo_offline_validate_draft',
          {
            repoRoot: options.repoRoot,
            input: {
              plan: summarizePlan(args.plan),
              draft: summarizeDraft(args.draft),
              autoRepair: args.autoRepair,
            },
          },
          async (paths) => {
            const contextEnvelope = await scanDemoOfflineContext(paths);

            if (!contextEnvelope.data) {
              throw new Error('Scan context did not return data.');
            }

            return validateIndustryDataDraft({
              plan: args.plan as never,
              draft: args.draft,
              context: contextEnvelope.data,
              autoRepair: args.autoRepair,
            });
          }
        );

        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to validate IndustryDataDraft.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
