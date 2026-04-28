import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { withToolAudit } from '../audit-log.js';
import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import { promoteCandidateScenario } from '../writer.js';

export interface RegisterPromoteCandidateToolOptions {
  repoRoot?: string;
}

export function registerPromoteCandidateTool(
  server: McpServer,
  options: RegisterPromoteCandidateToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_promote_candidate',
    {
      title: 'Promote demo-offline candidate',
      description: 'Promote a checked candidate scenario to the official generated scenario registry.',
      inputSchema: {
        candidateId: z.string().min(1),
        scenarioId: z.string().min(1),
        checksRunId: z.string().min(1),
        confirm: z.literal(true),
        replaceExisting: z.boolean().optional().default(false),
        cleanupCandidate: z.boolean().optional().default(false),
        activate: z.boolean().optional().default(true),
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
        const envelope = await withToolAudit(
          'demo_offline_promote_candidate',
          {
            repoRoot: options.repoRoot,
            input: {
              candidateId: args.candidateId,
              scenarioId: args.scenarioId,
              checksRunId: args.checksRunId,
              confirm: args.confirm,
              replaceExisting: args.replaceExisting,
              cleanupCandidate: args.cleanupCandidate,
              activate: args.activate,
            },
          },
          (paths) => promoteCandidateScenario(paths, args)
        );

        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to promote candidate scenario.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
