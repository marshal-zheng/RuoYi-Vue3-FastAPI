import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { z } from 'zod';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

import { issueFromUnknown } from '../errors.js';
import { errorEnvelope } from '../types.js';
import type {
  ImportDryRunSummary,
  OfflineStaticActivationResult,
  RuntimeValidationSummary,
  DemoOfflineArtifact,
  ToolEnvelope,
} from '../types.js';
import type { SemanticQualityReport, SemanticQualitySummary } from '../semantic/types.js';
import { generateOfflineStaticRuntimePackage } from '../offline-static/generate.js';

export interface RegisterGenerateRuntimeDemoToolOptions {
  repoRoot?: string;
}

interface CustomerRuntimeDemoResult {
  phase: OfflineStaticActivationResult['phase'];
  releaseId?: string;
  scenarioId: string;
  topicKey: string;
  activePointerPath?: string;
  previousPointerPath?: string;
  manifestPath?: string;
  provenancePath?: string;
  validationSummary?: RuntimeValidationSummary;
  dryRunSummary?: ImportDryRunSummary;
  semanticQualitySummary?: SemanticQualitySummary;
  semanticReportPath?: string;
  semanticQualityReport?: SemanticQualityReport;
  paths: string[];
}

function resolveRepositoryRoot(repoRoot?: string): string {
  return path.resolve(repoRoot?.trim() || fileURLToPath(new URL('../../../..', import.meta.url)));
}

function resolveDefaultTargetRoot(repoRoot?: string): string {
  return path.join(resolveRepositoryRoot(repoRoot), 'ruoyi-fastapi-frontend', 'dist-demo-offline');
}

function toCustomerRuntimeDemoResult(data: OfflineStaticActivationResult): CustomerRuntimeDemoResult {
  return {
    phase: data.phase,
    releaseId: data.releaseId,
    scenarioId: data.scenarioId,
    topicKey: data.topicKey,
    activePointerPath: data.activePointerPath,
    previousPointerPath: data.previousPointerPath,
    manifestPath: data.manifestPath,
    provenancePath: data.provenancePath,
    validationSummary: data.validationSummary,
    dryRunSummary: data.dryRunSummary,
    semanticQualitySummary: data.semanticQualitySummary,
    semanticReportPath: data.semanticReportPath,
    semanticQualityReport: data.semanticQualityReport,
    paths: data.paths,
  };
}

function toCustomerEnvelope(
  envelope: ToolEnvelope<OfflineStaticActivationResult>
): ToolEnvelope<CustomerRuntimeDemoResult> {
  return {
    ok: envelope.ok,
    summary: envelope.summary,
    ...(envelope.data ? { data: toCustomerRuntimeDemoResult(envelope.data) } : {}),
    ...(envelope.errors ? { errors: envelope.errors } : {}),
    ...(envelope.artifacts ? { artifacts: envelope.artifacts as DemoOfflineArtifact[] } : {}),
    ...(envelope.nextActions ? { nextActions: envelope.nextActions } : {}),
  };
}

export function registerGenerateRuntimeDemoTool(
  server: McpServer,
  options: RegisterGenerateRuntimeDemoToolOptions = {}
): void {
  server.registerTool(
    'demo_offline_generate_runtime_demo',
    {
      title: 'Generate customer offline runtime demo',
      description:
        'Customer-facing helper that generates, validates, dry-runs, and activates an offline-static runtime scenario package from a business prompt. Defaults to the current repository dist-demo-offline shell, activate=true, and projectCount=4.',
      inputSchema: {
        topic: z.string().min(1),
        businessDescription: z.string().optional(),
        projectCount: z.number().optional().default(4),
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
        const envelope = await generateOfflineStaticRuntimePackage({
          topic: args.topic,
          businessDescription: args.businessDescription,
          projectCount: args.projectCount ?? 4,
          targetRoot: resolveDefaultTargetRoot(options.repoRoot),
          activate: true,
        });
        const customerEnvelope = toCustomerEnvelope(envelope);

        return {
          isError: !customerEnvelope.ok,
          content: [{ type: 'text', text: JSON.stringify(customerEnvelope, null, 2) }],
          structuredContent: customerEnvelope,
        };
      } catch (error) {
        const envelope = errorEnvelope('Failed to generate customer offline runtime demo.', [
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
