import type { MockSimulationSession } from '../types';
import { MOCK_PROJECT_IDS, MOCK_SIMULATION_IDS, MOCK_VERSION_IDS } from '../_shared';

export const mockSimulationSessions = [
  {
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    projectId: MOCK_PROJECT_IDS.commandCenter,
    versionId: MOCK_VERSION_IDS.commandCenterReview,
    status: 'running',
  },
] satisfies MockSimulationSession[];
