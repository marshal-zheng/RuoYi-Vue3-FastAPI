import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { withToolAudit } from '../audit-log.js';
import { runChecks } from '../checks.js';
import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';

export interface RegisterRunChecksToolOptions {
  repoRoot?: string;
}

export function registerRunChecksTool(
  server: McpServer,
  options: RegisterRunChecksToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_run_checks',
    {
      title: 'Run demo-offline checks',
      description: 'Run fixed allowlist checks for candidate or promoted demo-offline scenarios.',
      inputSchema: {
        candidateId: z.string().optional(),
        scenarioId: z.string().optional(),
        profiles: z.array(z.string()).min(1),
        maxLogLines: z.number().int().positive().optional(),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: false,
      },
    },
    async (args) => {
      try {
        const envelope = await withToolAudit(
          'demo_offline_run_checks',
          {
            repoRoot: options.repoRoot,
            input: {
              candidateId: args.candidateId,
              scenarioId: args.scenarioId,
              profiles: args.profiles,
              maxLogLines: args.maxLogLines,
            },
          },
          (paths) => runChecks(paths, args)
        );

        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to run demo-offline checks.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
