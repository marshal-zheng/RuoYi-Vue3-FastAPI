import type { MockSimulationFrame } from '../types';
import { MOCK_SIMULATION_IDS, offsetMockTime } from '../_shared';

export const mockSimulationFrames = [
  {
    id: 'frame-001',
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    timestamp: offsetMockTime(0, -2),
    bandwidthMbps: 860,
    latencyMs: 18,
    alarmCount: 1,
  },
  {
    id: 'frame-002',
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    timestamp: offsetMockTime(0, -1),
    bandwidthMbps: 910,
    latencyMs: 16,
    alarmCount: 0,
  },
] satisfies MockSimulationFrame[];
