import type { ProjectPaths } from '../project-paths.js';
import type { CompiledDemoScenarioPackage, GenerationPlan, RuntimeScenarioMeta } from '../types.js';
import { writeCandidateScenario } from '../writer.js';
import type { DemoTargetAdapter } from './index.js';

export class SourceGeneratedTargetAdapter implements DemoTargetAdapter {
  readonly kind = 'source-generated' as const;

  constructor(
    private readonly paths: ProjectPaths,
    private readonly plan: GenerationPlan
  ) {}

  async writeCandidate(packageValue: CompiledDemoScenarioPackage, _meta: RuntimeScenarioMeta) {
    return writeCandidateScenario(this.paths, {
      scenarioPackage: packageValue,
      plan: this.plan,
      overwriteCandidate: true,
    });
  }
}
