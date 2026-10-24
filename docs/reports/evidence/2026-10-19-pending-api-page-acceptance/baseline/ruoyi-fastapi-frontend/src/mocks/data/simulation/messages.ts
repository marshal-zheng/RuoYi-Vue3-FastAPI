import type { MockSimulationMessage } from '../types';
import { MOCK_SIMULATION_IDS, offsetMockTime } from '../_shared';

export const mockSimulationMessages = [
  {
    id: 'message-001',
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    timestamp: offsetMockTime(0, -2),
    payload: {
      level: 'info',
      content: '仿真链路初始化完成',
    },
  },
  {
    id: 'message-002',
    sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
    timestamp: offsetMockTime(0, -1),
    payload: {
      level: 'warning',
      content: '遥测节点短时抖动，已自动恢复',
    },
  },
] satisfies MockSimulationMessage[];
