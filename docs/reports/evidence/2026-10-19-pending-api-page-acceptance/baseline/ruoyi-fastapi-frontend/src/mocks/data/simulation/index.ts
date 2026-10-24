import type { SimulationMockData } from '../types';
import { mockSimulationEvents } from './events';
import { mockSimulationFrames } from './frames';
import { mockSimulationMessages } from './messages';
import { mockSimulationSessions } from './sessions';

export const simulationMockData = {
  sessions: mockSimulationSessions,
  frames: mockSimulationFrames,
  messages: mockSimulationMessages,
  events: mockSimulationEvents,
} satisfies SimulationMockData;

export * from './events';
export * from './frames';
export * from './messages';
export * from './sessions';
