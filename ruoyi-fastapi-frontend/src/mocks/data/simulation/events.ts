import type { MockSimulationEvent } from '../types';
import { MOCK_SIMULATION_IDS, offsetMockTime } from '../_shared';

export const mockSimulationEvents = [
  {
    eventId: 'event-001',
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    triggerTime: offsetMockTime(0, -2),
    eventType: 'session_started',
  },
  {
    eventId: 'event-002',
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    triggerTime: offsetMockTime(0, -1),
    eventType: 'bandwidth_recovered',
  },
] satisfies MockSimulationEvent[];
