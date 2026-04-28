import { describe, expect, it } from 'vitest';

import {
  activeGeneratedScenarioId,
  candidateScenarioRegistry,
  defaultDemoScenario,
  generatedScenarioRegistry,
  getDemoScenarioPackage,
  validateDemoScenarioPackage,
  type DemoScenarioPackage,
} from './index';

describe('demo scenario registry', () => {
  it('loads default and official generated scenarios from the main registry', () => {
    expect(getDemoScenarioPackage('default')).toStrictEqual(
      validateDemoScenarioPackage(defaultDemoScenario)
    );
    expect(getDemoScenarioPackage('real-estate-project-demo')).toStrictEqual(
      validateDemoScenarioPackage(generatedScenarioRegistry['real-estate-project-demo'])
    );
    if (activeGeneratedScenarioId) {
      expect(getDemoScenarioPackage(activeGeneratedScenarioId)).toStrictEqual(
        validateDemoScenarioPackage(generatedScenarioRegistry[activeGeneratedScenarioId])
      );
    }
  });

  it('keeps candidate scenarios hidden unless validation mode is explicitly enabled', () => {
    const candidateScenario: DemoScenarioPackage = {
      ...defaultDemoScenario,
      scenario: {
        id: 'candidate-only-demo',
        name: 'Candidate Only Demo',
        version: '0.1.0',
        fingerprint: 'candidate-only-demo-v1',
      },
    };

    candidateScenarioRegistry[candidateScenario.scenario.id] = candidateScenario;

    try {
      expect(() => getDemoScenarioPackage(candidateScenario.scenario.id)).toThrow(
        'Demo scenario "candidate-only-demo" is not registered.'
      );
      expect(
        getDemoScenarioPackage(candidateScenario.scenario.id, {
          allowCandidateScenarios: true,
        })
      ).toStrictEqual(validateDemoScenarioPackage(candidateScenario));
    } finally {
      delete candidateScenarioRegistry[candidateScenario.scenario.id];
    }
  });
});
