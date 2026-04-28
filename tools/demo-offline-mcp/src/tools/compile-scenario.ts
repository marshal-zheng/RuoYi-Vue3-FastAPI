import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { summarizeDraft, summarizePlan, withToolAudit } from '../audit-log.js';
import { compileScenarioPackage } from '../compiler.js';
import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';

export interface RegisterCompileScenarioToolOptions {
  repoRoot?: string;
}

export function registerCompileScenarioTool(
  server: McpServer,
  options: RegisterCompileScenarioToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_compile_scenario',
    {
      title: 'Compile demo-offline scenario',
      description:
        'Compile a validated IndustryDataDraft into a deterministic DemoScenarioPackage without writing files.',
      inputSchema: {
        plan: z.record(z.unknown()),
        draft: z.record(z.unknown()),
        repairedDraft: z.record(z.unknown()).optional(),
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
        const draft = args.repairedDraft ?? args.draft;
        const envelope = await withToolAudit(
          'demo_offline_compile_scenario',
          {
            repoRoot: options.repoRoot,
            input: {
              plan: summarizePlan(args.plan),
              draft: summarizeDraft(draft),
              usesRepairedDraft: Boolean(args.repairedDraft),
            },
          },
          (paths) =>
            compileScenarioPackage({
              plan: args.plan as never,
              draft: draft as never,
              paths,
            })
        );
        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to compile demo-offline scenario.', [
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
