import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { compileScenarioPackage } from '../compiler.js';
import { scanDemoOfflineContext } from '../demo-scan.js';
import { createIssue, issueFromUnknown } from '../errors.js';
import { computeScenarioFingerprint } from '../hash.js';
import { ProjectPaths } from '../project-paths.js';
import { createGenerationPlan } from '../generation-plan.js';
import { errorEnvelope } from '../types.js';
import { writeCandidateScenario } from '../writer.js';
import {
  GENERATOR_VERSION,
  createDeterministicIndustryDraft,
  generateOfflineStaticRuntimePackage,
} from '../offline-static/generate.js';
import { createStableSeed, normalizeTopicKey } from '../offline-static/topic.js';

export interface RegisterGenerateDemoToolOptions {
  repoRoot?: string;
}

const targetSchema = z
  .object({
    kind: z.enum(['source-generated', 'offline-static']).optional().default('source-generated'),
    root: z.string().optional(),
    packageFormat: z.string().optional(),
  })
  .optional();

export function registerGenerateDemoTool(
  server: McpServer,
  options: RegisterGenerateDemoToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_generate_demo',
    {
      title: 'Generate demo-offline scenario',
      description:
        'Generate deterministic demo-offline data for source-generated development or offline-static runtime packages.',
      inputSchema: {
        topic: z.string().min(1),
        businessDescription: z.string().optional(),
        scenarioId: z.string().optional(),
        scenarioName: z.string().optional(),
        projectCount: z.number().optional(),
        target: targetSchema,
        activate: z.boolean().optional().default(false),
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
        const target = targetSchema.parse(args.target);
        if (target?.kind === 'offline-static') {
          if (target.packageFormat && target.packageFormat !== 'v2') {
            const envelope = errorEnvelope('offline-static target only supports v2 release packages.', [
              createIssue({
                path: 'target.packageFormat',
                code: 'offline_static_package_format_unsupported',
                severity: 'error',
                actual: target.packageFormat,
                expected: 'v2 or omitted',
                fixHint: 'Regenerate a v2 Release Store package; v1 active.json packages are no longer supported.',
                autoRepairable: false,
              }),
            ]);
            return {
              isError: true,
              content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
              structuredContent: envelope,
            };
          }

          const envelope = await generateOfflineStaticRuntimePackage({
            topic: args.topic,
            businessDescription: args.businessDescription,
            scenarioId: args.scenarioId,
            scenarioName: args.scenarioName,
            projectCount: args.projectCount,
            targetRoot: target.root ?? '',
            activate: args.activate,
          });

          return {
            content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
            structuredContent: envelope,
          };
        }

        const paths = await ProjectPaths.create({ repoRoot: options.repoRoot });
        const context = (await scanDemoOfflineContext(paths)).data!;
        const topicKey = normalizeTopicKey(args.topic, args.businessDescription);
        const seed = createStableSeed({
          topicKey,
          businessDescription: args.businessDescription,
          contractFingerprint: 'source-generated',
          generatorVersion: GENERATOR_VERSION,
        });
        const scenarioId = args.scenarioId?.trim() || `${topicKey}-source-demo`;
        const scenarioName = args.scenarioName?.trim() || `${args.topic} source demo`;
        const plan = createGenerationPlan(
          {
            brief: args.businessDescription || args.topic,
            industry: args.topic,
            scenarioId,
            scenarioName,
            targetCounts: {
              projects: args.projectCount,
              versionsPerProject: 1,
              sessionsPerProject: 1,
            },
          },
          context
        ).data!;
        const draft = createDeterministicIndustryDraft({
          topic: args.topic,
          businessDescription: args.businessDescription,
          topicKey,
          scenarioId,
          scenarioName,
          seed,
          projectCount: Math.max(1, Math.min(8, Math.floor(args.projectCount ?? 4))),
          contractFingerprint: 'source-generated',
          generatorVersion: GENERATOR_VERSION,
        });
        const compiled = await compileScenarioPackage({ plan, draft, paths });

        if (!compiled.ok || !compiled.data) {
          const envelope = errorEnvelope('Failed to compile source-generated scenario.', compiled.errors ?? []);
          return {
            isError: true,
            content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
            structuredContent: envelope,
          };
        }

        compiled.data.scenarioPackage.scenario.seed = seed;
        compiled.data.scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(
          compiled.data.scenarioPackage
        );
        const envelope = await writeCandidateScenario(paths, {
          scenarioPackage: compiled.data.scenarioPackage,
          plan,
          overwriteCandidate: args.overwriteCandidate,
        });

        return {
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to generate demo-offline scenario.', [issueFromUnknown(error)]);
        return {
          isError: true,
          content: [{ type: 'text', text: JSON.stringify(envelope, null, 2) }],
          structuredContent: envelope,
        };
      }
    }
  );
}
