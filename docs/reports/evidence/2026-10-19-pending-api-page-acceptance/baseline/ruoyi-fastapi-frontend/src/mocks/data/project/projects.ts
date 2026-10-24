import type { MockProject } from '../types';
import { MOCK_PROJECT_IDS, formatMockDateTime, offsetMockTime } from '../_shared';

export const mockProjects = [
  {
    projectId: MOCK_PROJECT_IDS.commandCenter,
    projectName: '联合指挥中心演示项目',
    status: 'active',
    createTime: formatMockDateTime(offsetMockTime(-18)),
    updateTime: formatMockDateTime(offsetMockTime(-1)),
  },
  {
    projectId: MOCK_PROJECT_IDS.trainingRange,
    projectName: '训练靶场链路验证项目',
    status: 'planning',
    createTime: formatMockDateTime(offsetMockTime(-9)),
    updateTime: formatMockDateTime(offsetMockTime(-2)),
  },
] satisfies MockProject[];
