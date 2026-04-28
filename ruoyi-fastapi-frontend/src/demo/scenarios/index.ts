import { defaultDemoScenario } from './default';
import { candidateScenarioRegistry } from './generated/candidates';
import { generatedScenarioRegistry } from './generated';
import { validateDemoScenarioPackage, type DemoScenarioPackage } from './schema';

const scenarioRegistry: Record<string, DemoScenarioPackage> = {
  [defaultDemoScenario.scenario.id]: defaultDemoScenario,
  ...generatedScenarioRegistry,
};

export interface GetDemoScenarioPackageOptions {
  allowCandidateScenarios?: boolean;
}

export function getDemoScenarioPackage(
  scenarioId: string,
  options: GetDemoScenarioPackageOptions = {}
): DemoScenarioPackage {
  const registry = options.allowCandidateScenarios
    ? {
        ...scenarioRegistry,
        ...candidateScenarioRegistry,
      }
    : scenarioRegistry;
  const scenarioPackage = registry[scenarioId];

  if (!scenarioPackage) {
    throw new Error(`Demo scenario "${scenarioId}" is not registered.`);
  }

  return validateDemoScenarioPackage(scenarioPackage);
}

export { defaultDemoScenario };
export { candidateScenarioRegistry } from './generated/candidates';
export { generatedScenarioRegistry, realEstateProjectDemoScenario } from './generated';
export { activeGeneratedScenarioId } from './generated/active';
export * from './schema';
