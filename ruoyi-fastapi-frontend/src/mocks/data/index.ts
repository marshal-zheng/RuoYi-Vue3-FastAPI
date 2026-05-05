import type { MockDataset } from "./types";
import { MOCK_DATASET_VERSION, MOCK_REFERENCE_TIME } from "./_shared";
import { authMockData } from "./auth";
import { deviceMockData } from "./device";
import { projectMockData } from "./project";
import { simulationMockData } from "./simulation";
import { systemMockData } from "./system";

export const mockDataset = {
  version: MOCK_DATASET_VERSION,
  referenceTime: MOCK_REFERENCE_TIME,
  auth: authMockData,
  system: systemMockData,
  device: deviceMockData,
  project: projectMockData,
  simulation: simulationMockData,
} satisfies MockDataset;

export * from "./_shared";
export * from "./auth";
export * from "./device";
export * from "./project";
export * from "./simulation";
export * from "./system";
export * from "./types";
