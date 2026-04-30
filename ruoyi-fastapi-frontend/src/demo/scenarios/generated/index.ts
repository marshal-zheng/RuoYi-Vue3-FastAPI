import type { DemoScenarioPackage } from '../schema';
import { activeGeneratedScenarioId } from './active';
import { realEstateP0AcceptanceDemoScenario } from './real-estate-p0-acceptance-demo';
import { realEstateProjectDemoScenario } from './real-estate-project-demo';
import { defenseSoftwareDeliveryQmDemoScenario } from './defense-software-delivery-demo';
import { smartMarketOperationsDemoScenario } from './smart-market-operations-demo';

export const generatedScenarioRegistry: Record<string, DemoScenarioPackage> = {
  [realEstateP0AcceptanceDemoScenario.scenario.id]: realEstateP0AcceptanceDemoScenario,
  [realEstateProjectDemoScenario.scenario.id]: realEstateProjectDemoScenario,
  [smartMarketOperationsDemoScenario.scenario.id]: smartMarketOperationsDemoScenario,
  [defenseSoftwareDeliveryQmDemoScenario.scenario.id]: defenseSoftwareDeliveryQmDemoScenario,
};

export {
  activeGeneratedScenarioId,
  realEstateP0AcceptanceDemoScenario,
  realEstateProjectDemoScenario,
  smartMarketOperationsDemoScenario,
  defenseSoftwareDeliveryQmDemoScenario,
};
