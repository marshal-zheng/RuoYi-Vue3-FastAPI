import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { withToolAudit } from '../audit-log.js';
import { scanDemoOfflineContext } from '../demo-scan.js';
import { createGenerationPlan } from '../generation-plan.js';
import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';

export interface RegisterCreateGenerationPlanToolOptions {
  repoRoot?: string;
}

export function registerCreateGenerationPlanTool(
  server: McpServer,
  options: RegisterCreateGenerationPlanToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_create_generation_plan',
    {
      title: 'Create demo-offline generation plan',
      description:
        'Create a reviewable generation plan from an industry brief and the scanned demo-offline context.',
      inputSchema: {
        brief: z.string().min(1),
        industry: z.string().optional(),
        scenarioId: z.string().optional(),
        scenarioName: z.string().optional(),
        scope: z.array(z.enum(['project', 'simulation'])).optional(),
        targetCounts: z
          .object({
            projects: z.number().int().positive().optional(),
            versionsPerProject: z.number().int().positive().optional(),
            sessionsPerProject: z.number().int().positive().optional(),
          })
          .optional(),
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
          'demo_offline_create_generation_plan',
          {
            repoRoot: options.repoRoot,
            input: {
              brief: args.brief.length > 160 ? `${args.brief.slice(0, 160)}...` : args.brief,
              industry: args.industry,
              scenarioId: args.scenarioId,
              scenarioName: args.scenarioName,
              scope: args.scope,
              targetCounts: args.targetCounts,
            },
          },
          async (paths) => {
            const contextEnvelope = await scanDemoOfflineContext(paths);

            if (!contextEnvelope.data) {
              throw new Error('Scan context did not return data.');
            }

            return createGenerationPlan(args, contextEnvelope.data);
          }
        );
        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to create demo-offline generation plan.', [
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
