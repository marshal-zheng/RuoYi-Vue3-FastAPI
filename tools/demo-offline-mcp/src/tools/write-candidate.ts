import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { summarizePlan, summarizeScenarioInput, withToolAudit } from '../audit-log.js';
import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import { writeCandidateScenario } from '../writer.js';

export interface RegisterWriteCandidateToolOptions {
  repoRoot?: string;
}

export function registerWriteCandidateTool(
  server: McpServer,
  options: RegisterWriteCandidateToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_write_candidate',
    {
      title: 'Write demo-offline candidate',
      description: 'Write a compiled scenario package to the generated candidate area.',
      inputSchema: {
        scenarioPackage: z.record(z.unknown()),
        plan: z.record(z.unknown()),
        overwriteCandidate: z.boolean().optional().default(false),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (args) => {
      try {
        const envelope = await withToolAudit(
          'demo_offline_write_candidate',
          {
            repoRoot: options.repoRoot,
            input: {
              scenarioPackage: summarizeScenarioInput(args.scenarioPackage),
              plan: summarizePlan(args.plan),
              overwriteCandidate: args.overwriteCandidate,
            },
          },
          (paths) =>
            writeCandidateScenario(paths, {
              scenarioPackage: args.scenarioPackage as never,
              plan: args.plan as never,
              overwriteCandidate: args.overwriteCandidate,
            })
        );

        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to write candidate scenario.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
