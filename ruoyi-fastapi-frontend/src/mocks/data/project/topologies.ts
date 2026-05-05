import type { MockTopology } from '../types';
import {
  MOCK_PROJECT_IDS,
  MOCK_TOPOLOGY_IDS,
  MOCK_VERSION_IDS,
  formatMockDateTime,
  offsetMockTime,
} from '../_shared';

export const mockTopologies = [
  {
    id: MOCK_TOPOLOGY_IDS.commandCenterBaseline,
    projectId: MOCK_PROJECT_IDS.commandCenter,
    versionId: MOCK_VERSION_IDS.commandCenterBaseline,
    graph: {
      nodes: [
        { id: 'gateway-1', label: '指挥网关', type: 'gateway' },
        { id: 'console-1', label: '态势终端', type: 'terminal' },
      ],
      edges: [{ source: 'gateway-1', target: 'console-1', label: '千兆以太网' }],
    },
    updateTime: formatMockDateTime(offsetMockTime(-8)),
  },
  {
    id: MOCK_TOPOLOGY_IDS.commandCenterReview,
    projectId: MOCK_PROJECT_IDS.commandCenter,
    versionId: MOCK_VERSION_IDS.commandCenterReview,
    graph: {
      nodes: [
        { id: 'gateway-1', label: '指挥网关', type: 'gateway' },
        { id: 'sensor-1', label: '遥测节点', type: 'sensor' },
      ],
      edges: [{ source: 'sensor-1', target: 'gateway-1', label: '1553B 总线' }],
    },
    updateTime: formatMockDateTime(offsetMockTime(-1)),
  },
  {
    id: MOCK_TOPOLOGY_IDS.trainingRangeBaseline,
    projectId: MOCK_PROJECT_IDS.trainingRange,
    versionId: MOCK_VERSION_IDS.trainingRangeBaseline,
    graph: {
      nodes: [
        { id: 'range-server', label: '仿真服务节点', type: 'server' },
        { id: 'range-client', label: '受训终端', type: 'terminal' },
      ],
      edges: [{ source: 'range-server', target: 'range-client', label: '控制链路' }],
    },
    updateTime: formatMockDateTime(offsetMockTime(-2)),
  },
] satisfies MockTopology[];
