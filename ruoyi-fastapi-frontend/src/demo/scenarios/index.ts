import { defaultDemoScenario } from './default';
import { validateDemoScenarioPackage, type DemoScenarioPackage } from './schema';

const scenarioRegistry: Record<string, DemoScenarioPackage> = {
  [defaultDemoScenario.scenario.id]: defaultDemoScenario,
};

export function getDemoScenarioPackage(scenarioId: string): DemoScenarioPackage {
  const scenarioPackage = scenarioRegistry[scenarioId];

  if (!scenarioPackage) {
    throw new Error(`Demo scenario "${scenarioId}" is not registered.`);
  }

  return validateDemoScenarioPackage(scenarioPackage);
}

export { defaultDemoScenario };
export * from './schema';
